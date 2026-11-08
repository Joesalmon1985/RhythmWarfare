# Rhythm Warfare: handover (rewritten 9 November 2026, end of the long run)

This is the single current handover. Everything above the line "Older material" is the long run of 7 to 9 November 2026 (stage A to E of `docs/parallel-development/LONG_RUN_PLAN.md`). Everything below that line is the earlier handover (Part A of 5 November: the three paths and the acting system; Part B of 3 November: the defense campaign and loadout), kept for the code that still lives in the repository. Where this part and the older material disagree, this part wins. Where `docs/parallel-development/RUN_LOG.md` and any older doc disagree, RUN_LOG wins and the older doc is stale.

Read next, in this order: `docs/parallel-development/RUN_LOG.md` (the whole run, newest at the bottom; its "START HERE" and "STOPPED HERE" sections are the resume points), `docs/parallel-development/LEAD_RULINGS.md` (rulings; 42, 42b and 43 are in the log or on `feature/shared-contracts`, see section 5), `docs/PICKUP.md` (setup, files not in Git), then the branch's own launch file (section 2).

**In one paragraph.** The campaign (Warehouse hub, Hospital, Mental Hospital, Spaceship, Hell, the three sister paths, the Bassment) is finished as stage A and lives on `feature/one-pc`. Beside it, kept apart on purpose, are two new playable things: eight Doom-geography worlds you walk while the rhythm game plays (`feature/doom-layout-worlds`), and a bedsit opening that leads to four raves, each with a cloakroom, a bar, a bass knob and a street race (`feature/bedsit-raves`). A fourth branch, `feature/shared-contracts`, holds the engine work both of them need. All of it was built and checked by agents with a virtual clock and a dummy audio driver. **No human has played any of it by hand, nothing has run on a phone, and nobody has listened to the music choices.** The next thing that matters is the owner playing `feature/one-pc`, then auditioning the Doom music.

## 1. Where things are (first screen)

| Branch | What it is | Worktree | Head | State |
| --- | --- | --- | --- | --- |
| `feature/one-pc` | The integration branch the owner plays. Stage A: the whole campaign, hub entrances, ways back, heralds and lit gates, the DJ-style transitions over the 61 tracks, art packages, camera clearance, the A7 Bassment, the viewpoint fix, the wiring step, the APK work. | `MusicGame-onepc` | see RUN_LOG's close (the head moves with each log append; code last changed at `c341280a`) | Stage A complete and green. Last recorded full suite: 160,445 checks, 0 failures, 0 SCRIPT ERROR (at `c341280a`, after the one-pc fixes). Since then only docs: RUN_LOG, LEAD_RULINGS, the two PR drafts, this handover. Waiting for the owner to play it. |
| `feature/shared-contracts` | Engine contracts both feature branches merge from: hold pitch and split voids, walk pace (rulings 42 and 42b), observe-once, the rail check's worst case (ruling 43), the herald-look fix for the card table, rain, geography worlds. | `MusicGame-contracts` | `e6a0383e` (final) | Green at `363e7a21`: blackjack 32803, heralds 430, camera 48, story_player 2868, rail_paths 652, transition 17579, run_ 16706, playtest 2993, story 52991, track 3164, weather 201, test_geography 283. `e6a0383e` adds only LEAD_RULINGS 39 to 43. Merged into both feature branches. |
| `feature/doom-layout-worlds` | Eight one-scene Doom-geography worlds (Warehouse/Floor, Copper Bar, Chill-out Lounge, DJ Booth, Loading Dock, Balcony, Mothership, Underworld), round 1 polish, per-world music, the cuts test under ruling 42b. | `MusicGame-env` | `2d0ece7a` (final) | Round 2 polish A, B and C all merged (A at `53198462`), contracts `e6a0383e` merged, the paced cuts test rewritten to polish A's stay rail at `2d0ece7a`. Green at `53198462` (`leadlogs/env_pola_*.log`): choice_pitch 28, split_void 22, rail_paths 652, test_geography 299, heralds 430, camera 48, transition 17579, track 3164, weather 201, blackjack 32803, run_ 16695, playtest 2949, story 52991; at `2d0ece7a` doom 2867 and doom_cuts 42 (the commit touches one test and two docs). Rail check 8 scenes, 0 problems, 0 walk-off warnings. Draft PR body: `docs/parallel-development/pr_drafts/PR_doom_layout_worlds.md`. |
| `feature/bedsit-raves` | The bedsit opening, four raves (Space, Magic, Dinos, Transport), the card table in the room, the street races, play round 2 (touch turns, tappable way out). | `MusicGame-play` | `b815ab45` (final) | Green at `b815ab45`, all 23 filters (`leadlogs/play_c2_*.log`): blackjack 10622, bedsit 425, the four raves, race 3616, run_matrix 1945, cloakroom 3062, bar 398, activity_modes 149, minigame 251, weather 201, test_geography 299, choice_pitch 28, heralds 430, camera 48, story_player 2868, rail_paths 652, transition 17579, run_ 17414, playtest 3569, story 53147. Draft PR body: `docs/parallel-development/pr_drafts/PR_bedsit_raves.md`. |

Two more branches matter. `main` is untouched by the run: **it moves only on the owner's word, after the owner has played `feature/one-pc`.** The agents' `wip/` branches are checkpoint branches; the lead merges them, `--no-ff`.

**The two feature branches are kept SEPARATE from `feature/one-pc` by plan.** They are not merged into it, and not into `main`. They get draft pull requests whose bodies must disclose the reviewers' lists and every placeholder (section 4). The GitHub CLI is not installed, so the lead could not open the PRs; both bodies are committed under `docs/parallel-development/pr_drafts/` with compare links for the owner to paste (or install `GitHub.cli` with winget and run `gh pr create --draft`). Both feature branches merge *from* `feature/shared-contracts`, never the other way round (the herald-look fix went onto contracts by cherry-pick for that reason).

Push policy, unchanged: integration branches are pushed after every verified merge, `wip/` branches at checkpoints, nothing to `main` until the owner says, no force-push. Agents never push or merge. Never in Git: the 61 recordings and every track pack, any WAD (`*.wad` and `/doom II wads/` are in `.gitignore`), the Doom renders, the APK and `build/`.

The older `docs/doom/LAUNCH.md` and `docs/bedsit/LAUNCH.md` live only on their feature branches (not on `feature/one-pc`). Read them with `git show feature/doom-layout-worlds:docs/doom/LAUNCH.md` and `git show feature/bedsit-raves:docs/bedsit/LAUNCH.md`. The Doom one is partly stale (see section 5). `docs/doom/MUSIC.md` and the per-scene notes `docs/doom/scenes/*.md` are on the Doom branch too.

## 2. How to play each

All commands are for PowerShell. Each `.cmd` finds Git's bash itself, uses a play copy of the save in `rw-audio-work\play_userdata` (never the real save) and needs the track packs (`RW_TRACKS_DIR`, else `rw-audio-work\packs`). Each worktree has its own scripts, so run the one in the worktree of the branch you want.

**The campaign, stage A (`feature/one-pc`)**

```
& "C:\Users\joesa\Documents\Cursor\MusicGame-onepc\tools\dev\play_tracks.cmd" --run
```

Without `--run` it opens at the main menu. Expect the Warehouse club as the hub with its entrances and ways back, the quests, the transitions between the recorded tracks. Not heard by anyone.

**The Doom worlds (`feature/doom-layout-worlds`)**

```
& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd"
& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd" --scene doom_bar
```

The first starts in the Warehouse (`doom_warehouse`); `--scene doom_<id>` starts in any of the eight (`doom_warehouse`, `doom_bar`, `doom_lounge`, `doom_booth`, `doom_dock`, `doom_balcony`, `doom_mothership`, `doom_underworld`). It sets `RW_DOOM_WORLDS=1` and `RW_RUN_START`. Without the flag the game is the legacy campaign, untouched. Expect: you walk a first-person rail through one painted world while the rhythm game plays; three guides stand for ahead, left and right; touching one commits at the tap, walks the leg to the doorway at walking pace, shuts the frame and swaps to the next world (rulings 39, 42, 42b). The routing table is in `docs/doom/LAUNCH.md`. Each world now plays its own recorded track (section 4, music).

**The bedsit and raves (`feature/bedsit-raves`)**

```
& "C:\Users\joesa\Documents\Cursor\MusicGame-play\tools\dev\play_bedsit.cmd"
& "C:\Users\joesa\Documents\Cursor\MusicGame-play\tools\dev\play_bedsit.cmd" --rave space
& "C:\Users\joesa\Documents\Cursor\MusicGame-play\tools\dev\play_bedsit.cmd" --race space
```

Forms in the script: no argument = the bedsit facing north; `N`, `E`, `S` or `W` = start facing that way (a development aid); `--dev-keys` = number keys pick any choice on show; `--rave space|magic|dinos|transport` = start inside that rave (add `--fixed` for the bass already fixed); `--race space|magic|dinos|transport` = start in that rave's hangar, then touch the racer. F3 shows an overlay line ending `compass <f> theme <name>`. Touch or click: the left fifth turns left, the right fifth turns right, the bottom middle stays, the top middle leaves by the threshold you face, the middle of the picture is the room (the way out, once open). Arrow keys are the same four regions. The shortest path to the ending (Space rave, three activities, home, turn west, touch the door) is written tap by tap in `docs/bedsit/LAUNCH.md`, "The player's path to the ending".

**What has NOT been played by a human.** Nothing has been played on a phone. The bedsit by touch exists only in tests (`tests/test_bedsit_play.gd`, 177 checks at the time of the report) and in a virtual run (`tools/dev/bedsit_virtual_run.gd`: right, right, top into Magic, home, the facing checked in the save); only the Magic path was driven end to end, and the way-out test sets the flags directly. The Doom worlds were seen only in headless shots and virtual runs (`docs/shots/doom/`); 7 cuts were run headless and were right, but 16 of the 24 cuts have never run on the run scene. The raves' activities are tested in all four raves, never played on a screen. Nobody has listened to the bass unlock, the Doom music picks, the races, or the APK's re-encoded stems.

## 3. Tests and tools

**The suite.** From a worktree root, in Git Bash:

```
bash tools/test.sh                      # the whole suite; runs --import first; also the Python content tests
bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tests/run_tests.gd -- --filter <name>
```

The full one-pc suite takes about 25 minutes (RUN_LOG): run it in the background. The old "10 to 15 minutes" and "about 1 min" in the older material are stale.

**Always `--import` first** in a fresh worktree and after merging new assets: `bash tools/dev/godot.sh --headless --path . --import`. Failures of the kind "sheet not found" were un-imported sheets. New `class_name` scripts also need it.

**The SCRIPT ERROR counting rule.** The runner prints "0 failures" when a test dies of a parse error. A green result means: 0 failures AND zero lines containing `SCRIPT ERROR` in the log. Count them every time. The expected noise is a few deliberate lines: `test_trial` prints one "Parse JSON failed" (not a failure), the Ogg/JSON error lines are deliberate test inputs, and the story filter exits 139 (a segfault at shutdown AFTER "checks, 0 failures" and the RID-leak lines) on at least one worktree (section 4).

**Filter lists the lead used.** Contracts: `choice_pitch split_void test_geography weather heralds camera story_player rail_paths story run_ playtest track transition`. Env: `doom doom_cuts doom_views choice_pitch split_void heralds camera rail_paths test_geography weather track transition run_ playtest story`, plus the rail check. Play: `bedsit space_rave magic_rave dinos_rave transport_rave race run_matrix cloakroom bar activity_modes minigame blackjack weather test_geography choice_pitch heralds camera story_player rail_paths run_ playtest story`. Counts change with every merge; read the newest in RUN_LOG and do not trust any number copied here.

**The per-worktree godot.sh lock.** `tools/dev/godot.sh` gives each worktree its own `user://` folder (so worktrees can run at once) and a lock: inside one worktree, one Godot at a time. A lock whose owner has died is cleared. A waiter gives up after `RW_GODOT_WAIT` seconds (default 3600) with exit 75. **A virtual run with `RW_RUN_UNTIL_PHASE` does not quit after it prints its summary** (the suites' runner is unaffected): it kept the `MusicGame-envmusic` lock for three hours on 9 November and blocked another agent until the lead ended the process. After such a run, find and stop the Godot process yourself. `RW_GODOT_SHARED=1` goes back to one machine-wide lock and the real user folder.

**The rail check.** `bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/story/check_rail_paths.gd -- res://content/run/doom/run.json` checks the Doom run (gated: 8 scenes, 0 problems at the last record). With no arguments it checks the whole main run (not gated by any suite). It now also prints one `WALKOFF` line per leg with its length, bars and pace, `WARN` when a leg needs more than 8 bars, and takes `--bpm=`. Under ruling 43 it measures from every place the rail can stand on and reports the longest ("worst case of n rail places; choice place ..."); a test asserts its metres equal the engine's longest leg within 0.05 m. An earlier version measured from the choice place or home and under-reported (Warehouse to Bar leg: 5.5 m from `wh_ref`, 20.9 m from `wh_fence`, the place the engine measures from); RUN_LOG's older WALKOFF figures predate the fix. The Doom scenes are to be re-measured when the polish batch lands.

**Generators.** Run these after a merge that touches their inputs, then `--import`, then the suites.
- `python tools/run/make_doom.py` regenerates the Doom overlay (`content/run/doom/`). `python tools/run/make_scenes.py --doom` does it as part of the normal generation. Per-scene rebuild lines are in `docs/doom/LAUNCH.md`.
- `python3 tools/run/make_bedsit.py --bedsit` regenerates the bedsit path, themes and routes; it keeps the blocks `tools/story/build_*_rave.py` write.
- `python tools/run/make_hotspots.py` regenerates the hotspot content and `docs/VISUAL_COVERAGE.md`.
- **If a merge conflicts in generated content** (`content/paths/bedsit/run.json`, `hotspots/{magic,dino,transport}_rave.json`, `docs/shots`): take either side and rerun the generator. Never hand-merge it.
- `python tools/audio_import/build_android_packs.py` builds the phone bundle (next item).

**The APK and the track packs.** Stage E is done up to the phone. `build_android_packs.py` re-encodes the 61 packs (4.6 GB on disk; Ogg about 500 kbps plus 684 MB of previews and reports) with ffmpeg libvorbis `-q:a 4`, 48 kHz stereo, lengths identical, into a 1,027 MB bundle in the git-ignored `/track_packs/` (each stem with an `importer="keep"` `.import`). The Android preset includes `track_packs/*/track.json`. `RunTrackScenes.packs_root` falls back to `res://track_packs` when `RW_TRACKS_DIR` is unset and `user://track_packs` is absent; the bundled path stays `res://` (fix `fa43278c`). The full debug APK is `MusicGame-apk/build/android/RhythmWarfare-debug.apk`, 1,225,141,764 bytes, export exit 0, 256 stems and 61 `track.json` listed in the zip; `tests/test_run_tracks_bundled.gd` has 4 checks and prints a counted SKIP where there is no bundle. Export command, from a worktree root after `--import`: `"C:/Users/joesa/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe" --headless --path . --export-debug "Android" build/android/RhythmWarfare-debug.apk`. The plan and the measurements are `docs/APK_61_TRACKS.md`. **Never commit the packs, the bundle or the APK.** Not done: nothing installed or run on a phone (latency, memory, load time, whether stems load from the APK's `assets`), `-q:a 4` not auditioned, no release keystore. This APK is built from the stage A work; whether it should carry the two feature branches is the owner's call.

## 4. Known limits, honestly (one list per branch)

Sources: the lead's "Known gaps carried", the two independent reviews, the lead's own looks at the polish sheets, all in RUN_LOG.

### `feature/one-pc`

- **Whole-run rail check: 84 scenes, 533 problems, exit 1.** All pre-existing; none come from the walk pacing. Gospel scenes report 44 each ("the eye is in the ceiling of bank_night" along the jordan moves), night_one warehouse 11, balcony 6, booth 7, underworld 3/2/2/6, ward.exit 2, ward_late 3, stub.end 7. No suite gates this check for the main run. An owner or next-run item, not fixed in the run.
- The Floor's four gates are hidden from the booth in the route window (a placement pass is owed). 18 hidden herald samples and 5 unseen ways back are pinned in `KNOWN_HIDDEN` and `KNOWN_BACK_UNSEEN`.
- Legacy people are below ruling 36's standard (package A2, the people re-bake, not done). Gospel p5 over the exposure rule. A7's door readability. No sound cues. Nobody has listened to the transitions or any track.
- `hospital_late` and `ward_late` loop with no ending: the owner's 6 November decision, declared in `content/narrative/graph.json` (`late_loops_have_no_ending`).
- Housekeeping: 21 merged local branches; the MIDI zip is undecided (the owner's call); the coverage audit was not re-run; `test_trial` prints one "Parse JSON failed" line.
- Reviewer's verdict on one-pc: "not yet hand-to-a-friend", chiefly for the missing human play and this handover. Its red items (heralds order dependence, the walk's "245 glances for 252 blocks", the silent skip, the late loops) were fixed in `c341280a`; the walk bug was real (`RunJourney._herald_blocks` never cleared on `lap_start`).
- The old handover's claim "everything is on main" is stale.

### `feature/shared-contracts`

- Engine hooks not built: a per-void "glow, no haze" key. Today the engine's haze over a connected void darkens what should glow (lava goes dark red, the pool dark violet); the Underworld and Mothership work round it with a shore piece at the pit floor's level.
- Ruling 42b is a design change the owner may overrule: on a long leg the picture cuts after the drop (section 5).
- The story filter exits 139 at shutdown after "48770 checks, 0 failures" on the `MusicGame-envmusic` worktree; not checked on other branches or worktrees.
- A virtual run with `RW_RUN_UNTIL_PHASE` never quits (section 3). The fourth `doom_lounge` entry in that run's summary is very likely that stop logging the next scene's `track_start` before the summary; not verified on Doom content.
- No shipped map has a void; `void_top` over split voids is tested on fixtures only.

### `feature/doom-layout-worlds`

- **Every scene is a placeholder against its painting (ruling 36), but all eight crossed to "the painting's place" except the Booth.** Shots inside the exposure rule after round 2 (at `53198462`): Warehouse 23/23, Bar 24/27, Lounge 17/21, Dock 8/8, Balcony 8/8, Underworld 8/8, Mothership 8/8, Booth 2/8. Before round 2 (at `5029fba1`) they were wh 13/17, bar 4/21, lounge 4/13, booth 1/8, dock 4/8, balcony 0/8, underworld 8/8, mothership 8/8. The independent review of round 1 said: playable, all eight worlds load and cut, not at the painting bar for Balcony, Mothership, Booth, Lounge.
- **Geography is approximate.** There is no map data: the supplied `doom2.wad` is an IWAD with no geometry (3,342 lumps) and a complete `DOOM2.WAD` is still wanted. Six maps were invented from the paintings, two traced from the ian-albert renders; all carry `doom.approximate`. If a WAD arrives the converter takes it.
- Carried items by scene (the lead's looks at the round 2 sheets beside the paintings; the full notes are in RUN_LOG and `docs/doom/LAUNCH.md`): **Warehouse** reads as a big club hall (warm bar corner, red lounge wall, the crowd and the lit rig) but is still a vast blue hall, the void floor shows under the lamps in the reveals, the far walls were not moved (a MAP07 re-trace is needed), the stage guide is 64 px, the crowd sprites repeat. **Bar** is the closest to its painting; the blue passage reads flat, the water gloss is faint, three shots at contrast 0.38 to 0.40. **Lounge** has the sofa ring, rug and table in frame under the pitched hold (pitch -12); the coffers are a flat tile, the glass passage a blue panel, no vault, the Dock street grey behind its guide. **Dock** reads as a rainy brick alley; the street is a blue-grey mid-tone where the painting is black wet tarmac with sodium pools, the brick is bright, the club door is a flat magenta rectangle. **Balcony** reads as a rooftop deck under the moon; the facades are a toy-like grid of candy-coloured windows, the drop is not seen into, the deck has magenta grid lines, the two route doors are flat decals, the dish is a flat placeholder. **Booth** reads as a desk in a corridor to a violet door, but the room is a mustard foam tile box that repeats: the one scene still a box, 6 of 8 shots out of the rule, needs an art pass. **Underworld** reads as a lava canyon under a red sky; the lava is a yellow-orange river not a lake, the basalt stripes repeat, `hold_cave` and `route_left` are blue-grey corridors off the palette. **Mothership** reads as a bone ring walk over a glowing pool; the bone is violet-tinted not cream, the pool a corner not a lake, the arches flat decals. All 24 guides are painting crops after round 2 (the Booth guide seen from the Bar 71 px, the Mothership guides 74 to 84 px, the Warehouse stage guide 64 px).
- **Guides.** The smallest guide at any reference viewpoint is 62 px (Mothership), the smallest gap 191 px, no ring, beacon or marker anywhere, every sheet 256 px. 4 of 24 guides were procedural at the review. **Procedural guides are placeholders and are named so.**
- **Cuts.** `tests/test_doom_cuts.gd` proves Warehouse to Bar to Floor on the run scene (42 checks at `2d0ece7a`; since polish A's stay rail the Warehouse leg starts at `wh_ref`, 5.5 m, 2 bars, the swap on the boundary; the hold-past-the-boundary case of ruling 42b is proven in `test_geography`). 16 of 24 cuts never run on the run scene, so a cut sweep tool and one cut per scene are owed. Under ruling 42b the picture cuts after the drop on a long leg (the Lounge up leg 28.6 m, 7 bars; the Warehouse up leg 31.5 m, 8 bars).
- **Music is picked by title, not by ear.** Floor: Valley of the Shadows (Chase & Status remix); Bar: Warm Roller "Memory"; Lounge: In The Clouds; Booth: T-2000; Dock: Shostakovich; Balcony: Zephyr; Mothership: Phantasm; Underworld: Night Train. The picks came from titles, tempos and section structure read from each `track.json`. **The owner is to audition them and swap rows**: one line in `content/run/track_scenes.json` plus the row in `docs/doom/MUSIC.md`. A real track-to-track blend was seen in a two-cut virtual run (`doom_warehouse` to `doom_bar` to `doom_lounge`).
- Not covered: no selected or committed guide-state capture in any shot set; no wall-sightline test in the wh/bar/booth blocks; pause, restart and stumble are untested in Doom worlds; Dock `route_ahead` holds on an empty street; the Lounge sofa needs the downward pitch hook; the rooms are still much larger than the paintings.
- `docs/doom/LAUNCH.md` was rewritten on 9 November (one worktree, `MusicGame-env`; per-world verdicts and carried items; the round 2 lines ticked by the lead at `2d0ece7a`). `cuts/warehouse_to_bar.jpg` predates the polish. No WAD or Doom texture is in Git.
- The Doom branch has contracts `e6a0383e` (the rail-check worst case, ruling 43, and the herald-look fix). Re-measured under the worst case: 8 scenes, 0 problems, 0 walk-off warnings (the 53.7 m Warehouse warning went when `wh_platform` left the rail places).

### `feature/bedsit-raves`

- **Placeholders.** The Magic, Dinos and Transport art, props and people are procedural placeholders; the manifests say so (`"placeholder": true`) and `tests/rave_theme_test.gd` asserts it. People are the Mothership's alien rigs recoloured, below ruling 36 (hi-vis with a hard hat for Transport, pastel with a horn for Magic, scaled colours for Dinos). The Space rave's people are the ring's alien rigs.
- **Races.** Every rave has a race scene (Space, Magic "The Moonlit Lane", Dinos "The Lava Ledge", Transport "The Wet Rally Street") on Space's rules and numbers, at Space's cell size not the 256 px class, with no race sounds. Entry to the race is a cut, not a drive-in; the race position is not saved. Race records persist across new runs as a career record (not in the brief; kept). The lead saw the Transport contact sheet only; the races agent looked at Magic and Dinos.
- **The way out shares the Transport door.** In the west facing the top of the door (fanlight, timetable) is the Transport threshold and the middle of the door is `bedsit.way_out` (ruling 41). The way out has no touch target from the other three facings. It is shown and touchable only after one rave's three activities.
- **Only the Magic path was driven end to end**, and the way-out test sets the flags directly. Nothing was played by a human. Not seen on a screen at all: the touch turns.
- Review items (Play round 2 fixed 1, 2, 3, 5 in part, 10, 12): (1) the bedsit could not turn by touch, (2) the way out was untappable, (3) coming home always faced north, (5) people recoloured rigs; labels were added but art is still placeholder; bar customers are now themed. Still open: (6) the cloakroom queue reads semi-transparent, unexplained (clear in `docs/shots/bedsit/transport/activities.jpg`); (7) no sound cues; (8) the bass unlock was never listened to; (9) race entry a cut, position unsaved; (11) no phone.
- The Bar and cloakroom, the card table: the card table runs in `replace` mode (ruling 40), the bar and cloakroom likewise. The ward card walk has `hold=4`.
- Progression gaps from the read-only check (9 November): no test that the opening finishes after one rave (since added: `tests/test_bedsit_opening_end.gd`, 66 checks); the activities were exercised in no non-Space theme until the raves landed (now covered by the theme tests).
- The four raves borrow the Mothership, Chill-out, Underworld and Dock geographies; the hotspot content is regenerated, never hand-edited.

## 5. Rulings in force, 35 to 43

Full text: `docs/parallel-development/LEAD_RULINGS.md` (35 to 41 on every branch that carries the file; 42 and 42b on `feature/shared-contracts`; 43 in RUN_LOG only, "Rail-check agent" entry). 41, 42, 42b and 43 are the lead's and open to the owner's overrule.

35. The owner, 7 November: more moments with the camera stationary (the rail arrives at a choice viewpoint and holds for the window); the red and green rings go: the artwork and its animation show a choice's state, never a uniform symbol over the world.
36. The owner, 7 November: the concept paintings (`art/reference/doom_worlds/` and `art/reference/standard/`) are the art bar; sprites are drawn like the Floor guide crop (about 230 px tall, 256 px sheets, dithered, readable costume, a face); placeholders are called placeholders in every report.
37. Decisions on the contracts' open questions: the bass knob runs in rhythm mode; leaving the bedsit goes at the next block boundary; race wins carry across runs; race energy loss never ends the run; save VERSION 3 (loader takes 2 and 3); the opening is its own path `content/paths/bedsit`; the race is an activity with a stage swap; the stem lock in `stem_transport.gd` accepted.
38. The owner, 8 November: every minigame happens in the same 2.5D world with the run's HUD, seamless, no separate screen; the pad strip carries the controls; the card table was converted (A8b).
39. A geography guide's tap is the decision: in a Doom world the first tap on a guide commits at that beat and the authored walk starts then; an untouched window keeps the default.
40. The owner, 8 November: the card table stays in `replace` mode as built (judging suspended while seated); B6 and B7 are superseded for it.
41. The lead, 9 November: the bedsit's way out opens once any ONE rave's three activities are done; a visit alone does not open it; once open it stays open.
42. The lead, 9 November: walk-outs take as long as the leg needs at no more than 3 m/s (bars = ceil(length / 3 m/s / bar), clamped 2 to 8); a longer leg is the scene's fault.
42b. The lead, 9 November: when the paced walk outlasts the phase boundary the music starts on time and the world swap waits for the hold's end, on a beat, never later than beat 32 of the next phase; the picture cuts after the drop on long legs. The alternative, a mid-leg cut on the drop, is open to the owner.
43. The lead, 9 November: the rail check measures the worst case over all rail places the rail can stand on (the engine really can start there); a scene with a long bad-place leg gets a warning and must add a hold or shorten the leg.

Ruling 38 and 40 supersede part of the older material below (the A14 to A16 rings and the 2D card table); 35 supersedes the rings.

## 6. Lessons for the next lead (from RUN_LOG)

- **Never `git commit -a` after a merge.** With unmerged paths it stages the conflict markers as resolved: `aeb4a827` on contracts shipped markers in `run_journey.gd` and was fixed forward in `5253d336`. After every merge run `git diff --name-only --diff-filter=U` and `grep -rl '^<<<<<<< ' src tests tools` before committing.
- **One merge per command**, so a conflict stops the chain.
- **`--import` after merging assets**, and in every fresh worktree. `git clean -fq` stray untracked `.import` and `.uid` files before a merge that brings the same ones.
- **Resolve `make_doom.py` and `test_doom_views.gd` merges by rebuilding from each side's blocks**, never by regex over conflict markers (burnt twice). Write Python patch scripts to files, not heredocs with Windows paths or apostrophes in Git Bash (the older material says the same).
- **Count SCRIPT ERROR lines** in every log (section 3).
- **Agents never push or merge**; the lead pushes. Agents commit a "WIP checkpoint" on their `wip/` branches at least hourly. When the 5-hour limit cuts agents off, resume them by message (their transcripts are kept) rather than restarting; at most four at once.
- **Models:** Sonnet by default (generators, scene data, tests, docs, checks); Opus for shared engine work and visual polish; the lead for merges, rulings, the independent review set-up and judging the sheets. A Sonnet agent ran out of turns repeatedly under machine load (the music package): the lead finished its verification.
- **Look at every sheet beside its painting** (ruling 36) before accepting a polish merge; the agents' own pass numbers are not enough. Polish C found the choice window was not happening at the reference viewpoint in the real run (the rail moves one place per passed block), and that the whole Underworld was lilac corridors in round 1.
- **Compare tool and engine.** The rail check under-reported legs until it was compared with the engine's own log line; check a check against the thing it checks.
- **A bisect belongs in a scratch worktree.** The blackjack regression was found by bisecting `329d6aa6`, `b3c784d6`, `0be1589d`; the contracts merge was the cause, not play round 2.
- **A virtual run with `RW_RUN_UNTIL_PHASE` holds the lock** until you stop it.
- **A merge conflict on generated bedsit content**: take either side, rerun `make_bedsit.py --bedsit`.
- **Agent reports are claims.** Spot-check against the log (the reviewers' spot-checks matched RUN_LOG exactly, which is why the numbers here can be trusted).

## 7. What to do next (the lead's ordered list, with what RUN_LOG records)

1. Fix or confirm the blackjack view on play (fixed by `75721c3c`; confirm the full play list on `b815ab45` and push).
2. Merge `wip/env-cuts-pace` into env: done (`d5535f65`).
3. Merge the round 2 polish A and B into env one at a time (`grep` for markers after each; `python tools/run/make_doom.py`; `--import`; the env list; the rail check); look at every contact sheet beside its painting and record the verdict. Polish C is merged (`43015e61`). Re-measure the Doom legs under the rail check's worst case.
4. Merge contracts into env (walk pace after `eace4db9`, rail check `5af6aef6`, herald-look `363e7a21`) and re-run.
5. Stage D close: draft PRs for the two feature branches (bodies disclose section 4 and every placeholder), refresh `docs/doom/LAUNCH.md`, copy RUN_LOG to the branches, update memory.
6. The owner: play `feature/one-pc`; audition `docs/doom/MUSIC.md`; rule on 41, 42, 42b and 43; decide the MIDI zip; say when `main` moves.
7. Later: a phone run; ears on the `-q:a 4` stems; a complete `DOOM2.WAD`; the per-void "glow, no haze" key; drawn art for the raves and the guides.

Filled at the close (9 November 2026): heads in section 1; polish A and B round 2 both merged into env (B before A; A at `53198462`), the lead's verdicts on all eight worlds are in RUN_LOG and `docs/doom/LAUNCH.md`; the draft PR bodies exist as files (above); env's final head is `2d0ece7a` (the cuts test fix after polish A changed the Warehouse rail), play's is `b815ab45`. Steps 3 to 5 of the list above are done; 6 and 7 are the owner's and the future's.

---

# Older material

Everything below was written on 3 and 5 November and is kept for the code it describes. The parts that the run superseded are marked "superseded" where they were cut or where a banner says so. Superseded in part: A14, A15 and A16 describe the red and green rings and the 2D card table (rulings 35, 38 and 40 replace both); the repo-size and export figures are of 5 November and 31 October.

# Part A: the three paths and the acting system

## A1. What is done, stage by stage

| Stage | What | Commits (first to last) | Notes |
| --- | --- | --- | --- |
| 1a | fourteen faces and fifteen directed acts in the pixel people, baked only for the directed people | `3caa067c`, `88df541e` | `docs/STORY_ART.md` "Acting" |
| 1b | the acting contract: `acting` on hotspots, `cast` on scenes and cinematics, `StoryCrowd.direct_actor`, validator | `a72384f9` | `docs/CONTINUOUS_RUN.md` "Acting in the run" |
| 1c | the silent HUD (no title card, captions, names, countdown, caption band); `RW_DEV_TEXT=1` restores them; the Bassment's ten creatures act | `713be82d`, `5bb0b9c8` | `docs/CONTINUOUS_RUN.md` "The silent HUD" |
| 1d | the acting pass on the five old worlds: 28 character hotspots plus the stranger, cast lines on all 36 scenes, 15 cinematics acted | `e82b9e8b`, `866b7aa2` | `tools/run/acting_data.py`; shots `docs/shots/acting/` |
| 2 | sister runs: `content/paths/<id>/`, relaxed graph rules, the three Warehouse portals, the tempo handoff, `paths` in the save, the home screen's path section, `beatshaper --path`, placeholders, the `stub` path | `5285f2ac`, `68a3f20c`, `6e30f6f2` | `docs/CONTINUOUS_RUN.md` "Paths" |
| 3 | The Life of Jesus (`gospel`): 17 scenes, 4 worlds, 4 maps, 130 people, 43 hotspots, two endings (`tomb`, `road`) | `91f0a611`, `b8bcad5e`, `16ee5aec`, `0ab74184`, `c230b0ff`, `c64a6b09` | `docs/paths/gospel.md` |
| 4 | The Mission Count (`squadron`): 14 scenes, 4 worlds, 3 maps, the Clause and the loop, one ending (`free`); the owner's 14 loops | `42c908c4`, `fbe0f69b`, `db342a11`, `3a9868e8`, `ad96378a`, `e2a9ca86` | `docs/paths/squadron.md` |
| 5 | The Ember Road (`ember`): 15 scenes, 5 worlds, 4 maps, flags that change later scenes, two endings (`quenched`, `kept`) and a setback | `461bc1c1`, `1ad2cb3b`, `91976d84`, `d995ede0`, `8f0d8b0e`, `dac0a5b5`, `97d361d4` | `docs/paths/ember.md` |
| 6 | this handover; README, CONTINUOUS_RUN, STORY_ART, MUSIC_IMPORT and MUSIC_HANDOFF brought up to date; the final whole-project check; the repo-size audit | the "Stage 6" commits | below |

How the stage 1 to 2 details differ from the plan, in the order they were written, is in the stage notes this file replaced (kept in git history: `git show e2a9ca86:docs/HANDOVER.md`). The ones that still matter are in A3.

## A2. What was verified, and what was not

### Verified (5 November 2026, this PC, Godot 4.5.1 console, Windows 11; the final whole-project run of Stage 6)

Superseded and cut: the 5 November table of results (73,712 checks and the per-path check_hotspots and walk_run results). Current counts are in `docs/parallel-development/RUN_LOG.md`; the commands that produced them are still valid (A7).

What the tests cover for the paths: `tests/test_run_paths.gd` (rates, relaxed rules, wrong-tempo pack refused, portals both ways, save migration, the handoff in both directions with `beat_s` before and after, the phase on the downbeat, cue times on the new grid,
the clock swap, the real scene entering the stub through the balcony and leaving by its ending), `test_gospel.gd`, `test_run_squadron.gd`, `test_run_ember.gd` (data, flags, cast, pieces, `hide`, acting in five states, the real scene through the real portal, every
ending), the per-path policy matrix in `test_run_matrix.gd` (each path under every tap policy and four skills), `test_story_acts.gd` (every directed person is baked in exactly the acts the data uses), `test_run_hud_silent.gd`, and the Python content tests
(placeholders, importer, gospel, directed actors). (The 5 November history of test counts is superseded and cut.)

Also verified earlier and not repeated now (still valid, nothing it covers has changed): the handoff recording (`docs/shots/run/path_handoff_check.txt`: beat grids 174 -> 124 -> 174 BPM, the new grid's first downbeat +2.9 ms from the old drums in, -6.5 ms out, every block fitting its stage
gains); the prebuild of a path's first stage in a cue-free guard (75 ms to 250 ms per map, none behind the closed frame); the balcony star opening the Gospel for real; the booth radio entering Squadron at 174 -> 140 and leaving at 140 -> 174; shots of every scene of
every path and of every character hotspot in five states, looked at by the agents (`docs/shots/{gospel,squadron,ember}/`, `docs/shots/acting/`).

### NOT verified (the honest list)

1. **Nothing has been played by hand and nothing has been heard.** No phone, no real output latency, no touch feel, no frame times on a phone (the maps were built on a desktop). The placeholders were measured (bass-forward, sub share), never auditioned; the Squadron gains come from
   measurements of the written loops, not ears. The owner's phone run (`How to run the phone check`, Part B) is still the first real test of anything in the game.
2. **Acts, faces, set pieces and the Golgotha staging have only been seen as still frames** from the virtual clock. Whether a player who is watching the pads sees an act at beat 50 and an outcome at beat 62 is unknown. Several pieces (`swell`, `long_shadow`, `river_rise`,
   `rider_shadow`, `drowned`, the Gospel's sky pieces) were validated and fired at their beats in tests; nobody looked at most of them on screen.
3. **No real Gospel or Ember loops exist.** 32 scenes play synthesised placeholders (17 Gospel, 15 Ember). Whether the owner's loops, when they arrive, will pass the importer is unknown: the Squadron ones needed `--max-error-ms 40` for six scenes and are 4-bar phrases.
4. **The tempo handoff and its clock fix were measured with the dummy audio driver only** (see A4); no real output latency.
5. **The Android and Windows exports predate all of this** (they predate even the loadout redesign, Part B item 17). Nothing was exported; the size of an export with the path packs was not measured (A8).
6. `tools/story/check_assets.py` covers the five old chapters and the three Squadron worlds, not the Gospel's or the Ember's maps (their art is checked by their own tests and `tools/story/check_map.gd`).
7. The pause menu's "Leave this path" button was built and tested through the scene but not looked at on a real screen.

## A3. Divergences from the plan, gathered from the stage notes

Plan-wide (stages 1 and 2):
* The pose key `fwd` (a forward bend) was added to the pixel rig; `point` and `stare` keep their old default faces; the plan's `StoryCrowd.direct(...)` is `direct_actor` (the name `direct` was taken by the crowd's group directive).
* The wizard hotspots in the Warehouse (`warehouse.wizard`, `warehouse.chill.wizard`) have no `acting`: the wizard is a billboard thing, not a baked person.
* The "committed" flash is one beat, not two; a result is seen about three beats at best before the passage frame closes over a route to another world, so the strongest act of a route-leaving hotspot is in its `success` / `failure`, briefly.
* The portals are gated so they fit the 2 to 4 rule: the star needs `wh_saw_floor`, the ember `wh_vip_pass`, the radio nothing.
* Path placeholders are WAV, not Ogg (the format `beatshaper.py import` writes; Ogg cannot promise a sample-exact loop), with MIDI beside them.
* The way back from a path is the world-change arrival (door, walk to the floor), not `trial_leave`'s fresh rail, because a path may leave the camera in another sector. `path_enter` marks a path's worlds in `paths`, never in `reached`.
* The engine got `grid_origin` so cues sit on the new tempo's grid counted from the handoff downbeat.
* Four directed people (`g07`, `g08`, `court_g06`, `e04`) belonged to groups the run never brings in; `StoryCrowd.ensure_present` fades them in.

The Gospel (stage 3): one map per world means the plan's four maps became four maps with 17 views (a view per scene), `galilee_shore` is the Jordan's alone and the lakeshore is on `hillside`; J00 and J14 have a harmless second hotspot (the shepherd, the women) because the
contract needs two in every scene; a path's exit scene may lead on inside its world and to a non-entry scene of it; for a path `check_hotspots.py` wants some hotspot leading to a route, not an exit of its own; the sky pieces of Golgotha are billboards at 12 m (they dim the sky
behind the hill, not the people in front).

The Mission Count (stage 4): three maps, not four (the night bomber is a room of `airfield`; `base` and `air` share a map); the loops are 16-beat (4-bar) phrases, not 8 bars, so a phase is four laps and each lap brings a new layer (the path's own `stages` in run.json, data only);
six scenes needed a 40 ms MIDI tolerance; the plan's `object` touches whose success is a route are `exit` hotspots here (the validator wants an exit anchored on a thing or a doorway per route); exit scenes route in their own world only with `loop: true` and the depth rule is
lifted; there is no placeholder music at all; the booth portal gained a visible radio and a bomber's shadow (Night One props).

The Ember Road (stage 5): five worlds, not four (the plan's `north` world listed two maps, so it is split into `north` and `deeps`); the default exit of a scene is an invented lit way on where the plan lists two non-exit touches (E03, E06 to E09, E11 to E14); E00 has a second touch
(the Ember in its bowl); the grandmother lies and sleeps instead of offering; the gate's laughing mouths are a set piece, not an act; "alone" and "lost companions" are `hide` cast lines (a new kind of cast line); directed companions are per-room instances of one `person`;
the Birch Hall's and the lake's setbacks go to the High Pass across a world border as `loop` routes; the placeholders are WAV at 145 BPM.

## A4. Known problems and weak spots

**Audio.**
* *The 88 ms phase-change offset: found and fixed (commit `56adc157`, after the stages).* After a tempo handoff, `RunAudio._swap_clock` set the song base to the downbeat, but a new stream's position reads one mix period ahead after its first mix, so the clock (cues, voices, judge) ran that far ahead
  of the sound from every swap on: 88.5 ms with the dummy driver, estimated 5.9 to 20 ms on a device. `song_base` is now `t - mix_period`; `check_run_audio.py` asserts every in-path phase boundary within the dummy driver's 29.4 ms floor; the handoff recording went from -88.58 ms (spread 95.1 ms) to -6.12 ms
  (spread 12.6 ms) on the stub and -5.92 ms (spread 5.9 ms) on the real Gospel. Measured with the dummy driver only: whether a phone's handoff is tight is still to be heard.
* *Squadron bass* (since lifted at the bus level, without touching the loops: A10). C05 and C06 have a short loud bass transient on a quiet body (peak-limited: RMS about -23 to -25 dBFS; at stage 2 the bass sits below the drums); C03, C05, C06, C09 and C11 are mid-heavy (8 to 31 % of the bass under 90 Hz). Nothing was edited; a re-export with the
  transient tamed, or a game-side limiter, would give more.
* *Placeholders on a phone speaker.* Bass-forward by measurement (RMS: drums -20 to -21, bass -11 to -12, pad -28 dBFS; at least 45 to 50 % of the bass under 90 Hz); whether that is prominent enough on a phone speaker is the owner's to judge.

**Shots and art the agents were not happy with** (all are looked-at stills, in `docs/shots/`):
* Gospel: the acting strips of route-leaving hotspots (`gospel_jordan_wilderness_*`, the exits) show their success and failure panels inside the passage frame, so the tempter's `recoil` and `laugh` do not read; for `galilee.capernaum.family` and `galilee.fishermen` the committed and success
  panels differ little from `available`; the dusk and night views (J09, J12) are dark and the grove's far crowd is a few pixels; `wall_hill` and `wall_columns` read as flat bands and heavy shadow; the skies are built from large dither cells at this resolution; the grove's torch and the
  Bethlehem fire are lights, not animated art.
* Squadron: `route_cNN` where the rail's wandering camera looks at a wall or the ceiling at beat 56 (C03, C04, C05, C06 above all: the hotspots then show as edge beacons, touchable but not pretty); the quay (`node_c12`, `route_c12`, the sentry's and the boat's acting strips) shows the neutral
  coast through its gap as a glitchy block of dither and the fishing boat reads as a dark hulk; the flight line's sandbag berm is very loud orange; C04's lever is hard to find from the home camera; weak art: `thing_tent_flap` (a cross on a white sheet could be read as a flag), `thing_truck`,
  `thing_staff_car`, `thing_medkit`, `wall_hangar`, `wall_stucco`; the gunner reads as a small person in a helmet more than a boy, the MP's helmet is a white dome, the patient's head bandage a turban, the ribbons and stripes are small.
* Ember: `route_*` shots of the dark scenes (Deep Halls, Falls, the Keeper) have small dim people at the default camera; `node_hollow_ford` has Bram and his lantern at the edge; E12 and E13 have Bram and the Hollow One at the edges of a very dark cavern, and the `swell` and `long_shadow`
  pieces are seen late in the phase and were not shot; the Hollow One's skin reads cyan in the teal marsh (the light's colour, not the rig's).
* Stage 1d: `underworld_court_queen` (hidden in a crowd of dancers), `ward_dorm_sleeper` (selected and committed acts do not show), `ward_late_exit_stare` (faces only), the two bouncers and `mothership_exit_exam` (panels inside the passage frame).

**Engine and tool limits.**
* A hotspot whose person belongs to a group the run never brings in anchors on nobody unless `ensure_present` is called; the Gospel's `late` group relies on cast lines. A new path author should check each acting hotspot's person exists in the room.
* The Warehouse portals are small, pulsing and gated; a first-time player may never find them (A6 question 5).
* The matrix, the walks and the checks all run on the virtual clock; real-time behaviour (frame times, GC pauses at a map build) is only measured for the prebuild.
* `walk_run.sh` and the capture scripts default to the Linux Godot path: set `GODOT` on Windows.

## A5. Backlog (not built)

1. ~~The Warehouse portal's changed look once a path has been finished (plan D10)~~: built in the visual polish (A9), `look.finished`.
2. The Warehouse wizards do not act (they are billboard things, not people); `RunActing.figure_motion` (the Bassment's) is the model.
3. Gospel and Ember maps in `check_assets.py`.
4. Nothing exercises the real-time audio on a path other than the stub handoff recording; a re-record with `tools/story/record_music.gd` through `warehouse.booth.radio` (140 BPM) and the bar ember (145) would extend `docs/shots/run/path_handoff_check.txt`.
5. Part B's backlog still applies to the defense campaign.

## A6. Open decisions for the owner

1. **Squadron timing: loosen or re-export?** C01, C02, C04, C08, C09 and C12 were imported with a 40 ms MIDI tolerance (their kick or snare hits sit 31 to 38 ms from the MIDI notes; the importer's default is 12 ms). Nothing was retimed. If hits feel late or early in those scenes, re-export
   from the DAW with the drums quantised, or accept it. C09, C11 and C14 have no snare note.
2. **Squadron loops are 4 bars, not 8.** They tile the 64-beat phase four times and the stage mix changes every lap (every 6.9 s), so the arrangement moves even though the loop does not. If 8-bar loops are wanted, they have to be re-exported; the importer takes either.
3. **Gospel and Ember need their real loops.** 17 and 15 prompts, verbatim, are in `docs/MUSIC_HANDOFF.md`; drop the exports in `content/imports/<path>/<scene>/` and run `beatshaper.py --path <id> apply ...`. Until then the placeholders are WAV (not Ogg), bass-forward and never auditioned.
4. **Judgement words.** PERFECT, GREAT and MISS are still drawn on the pads as feedback ("not story"). Decision: keep them, or remove them for the full silent-HUD intent (one flag in `RunPlay._on_judge_event`).
5. **Portal discoverability.** The star appears only after the floor has been seen from the balcony rail (`wh_saw_floor`) and the ember only after the stranger's VIP pass (`wh_vip_pass`); the radio is always there. Keep the gating (it fits the 2 to 4 rule) or make the portals easier to find, e.g. a second hint
   in the room or a home-screen shortcut for review.
6. **A look for a finished path** (plan D10, A5 item 1): build it, or leave the home screen's "Endings found" as the only trace.
7. **Squadron's thin bass** in C05 and C06 (and mid-heavy C03, C09, C11): re-export, or a game-side limiter.
8. **The Gospel path's subject.** It follows a public-domain source with alternative-history branches and never shows the player; no painting or film is depicted (plan D2). Whether to ship it, and in which stores or ratings, is the owner's call and was not examined by the agents.
9. **Repo size** (A8): keep the placeholder WAVs in git, or git-ignore them and regenerate by script.
10. **Two laps per path scene** (A12): keep them, revert a path or a scene (one value in the data), or ask for a drums-cue block inside lap 2 (four bass-cue blocks in a row is the current rule). Also: is the weaker player's harder economy (A12 section 3) acceptable, or should the energy numbers be eased?

## A7. How to run the checks (the short list; the full list is `README.md`)

```
bash tools/test.sh                                        # whole suite (10 to 15 minutes for the Godot part on this PC)
python3 tools/run/check_hotspots.py [--path gospel|squadron|ember]
GODOT=<godot console binary> bash tools/run/walk_run.sh --path gospel      # also squadron, ember; no --path: the five old worlds (all need a display)
python3 tools/story/check_assets.py
python3 tools/content/music_handoff.py                    # regenerate docs/MUSIC_HANDOFF.md
```

## A8. Repo size

Measured on 5 November 2026 (report only: no history was rewritten and no tracked file was deleted).

| What | Number |
| --- | --- |
| Repository, packed (`git count-objects -vH`) | 852 MiB `size-pack` (+9.5 MiB loose); all reachable blobs at `HEAD` 850 MiB packed |
| The same at the plan's starting commit `5efcfd2` | 598 MiB packed (857 MiB raw) |
| Growth since the plan | +252 MiB packed (+342 MiB raw): packs of the paths 116 MiB, new story art (textures, sprites, people sheets) 90 MiB, screenshots 49 MiB, everything else about 1 MiB |
| The paths' packs, packed in git (unique blobs) | Gospel 42.5 MiB (65.5 MiB raw), Ember 34.0 MiB (51.2 raw), Squadron 28.5 MiB (52.9 raw, the owner's real loops), `stub` 10.9 MiB (17.1 raw) |
| The same on disk in a working tree (`du`, no sharing) | `songs/packs` 445 MB in all: Gospel 146 MB (17 packs, 8.6 MB each), Ember 110 MB (15 packs), Squadron 54 MB (14 packs) |
| Largest single tracked file | 8.7 MB (`docs/shots/faces/mothership_after.jpg`); no tracked file is over 20 MB |
| Largest blob among the paths' packs | 2.8 MiB (one WAV stem); a placeholder pack is three 2.9 MB stems plus MIDI |

Git stores identical stems once (Gospel's 51 WAV files are only 23 distinct blobs), which is why the packed numbers are well under the working-tree ones. **Nothing is near GitHub's 100 MB per-file limit**; the repository as a whole (852 MiB) is under GitHub's 1 GB
"recommended" size and 5 GB soft limit but is the number to watch: the owner's real loops for 32 more scenes (Squadron's 14 added 28.5 MiB packed for 4-bar loops; 8-bar WAV loops would be about twice that each) would take it past 1 GB.

**Could the placeholders be git-ignored and regenerated?** They could. `python tools/content/make_path_placeholders.py <path> --force` is deterministic: regenerating Ember's packs into a scratch folder gave byte-identical `loops/*.wav` and `pack.json` to the committed ones (checked for two scenes; the
generator seeds by path and scene), and it takes about 12 s a path. The Gospel's and Ember's placeholders are 76.5 MiB packed (87 MiB with `stub`), about 10 % of the repository. What it would cost: the game, `tools/test.sh` and the walks fail on a fresh clone until the script has been run
for `gospel`, `ember` and `stub` (a `tools/test.sh` pre-step could do it); the tracked `.wav.import` files would also have to go or be regenerated; and a blanket ignore of `songs/packs/gospel_*` would also hide the owner's real imports, so each imported pack would need `git add -f` or an exception.
Ignoring them also does not shrink history (the 76.5 MiB stays in every clone until the history is rewritten, which is not recommended while other people's clones and the Android checkout exist).

**Recommendation.** Do nothing now. Keep the placeholders tracked until the owner's real loops arrive scene by scene; when a scene is imported, the placeholder pack is replaced (the importer's `apply` writes over it) (its old blobs stay in history; the real loop is added to the repository on top). If the repository nears 1 GB before then, ignore
and regenerate only `stub_*` and the placeholder packs that still carry `"placeholder": true`, add the generation step to `tools/test.sh`, and think about moving the real WAV loops to Git LFS or Ogg (Ogg cannot promise a sample-exact loop, which is why the importer writes WAV). Separately, **the export**: the presets used to pack everything (611 MB, 346 MiB of it proof shots) and, because of `content/.gdignore`, no `content/` at all, so a build could not start a run. Fixed (see `docs/REPO_SIZE.md`): exclude filters in both presets, `.gdignore` moved, the pack is now 240 MB and `tools/export_smoke.gd` proves the run, the paths and the story load from it. Part 2 then stored the packs' stems once per distinct sound in `songs/packs/_shared` (pack.json `stems` name `../_shared/...`; run `python3 tools/content/stems.py` after an import) and imports the dual-mono ones as one channel: tree 901 to 764 MiB, no new git blob, exported pack 184 MB (Ogg was tested and fails: `tools/content/ogg_check.py`). `docs/REPO_SIZE.md` also has the measured numbers, the history-rewrite option (commands, not run) and the recommendation (stop committing proof shots; do not rewrite history until the packs are final).


## A9. Visual polish (5 November 2026, after Stage 6)

A pass on the weak shots of A4, done by an agent from still frames on the virtual clock (worktree `MusicGame-paths2`). Every change below was looked at before and after; the pairs are in `docs/shots/polish/` (`before_*` / `after_*`, or one image with before on top / left).

**What changed**

| Weak point (A4) | Fix | Proof (`docs/shots/polish/`) |
| --- | --- | --- |
| Outcome acts of a route-leaving hotspot fell inside the closing passage frame (both bouncers, `mothership.exit.exam`, the Gospel J02 exits, ...) | A commit whose scene is left at the downbeat (its route, or the phase's route, is another scene) cuts the commit flash to half a beat (`RunActing.LEAVING_COMMITTED_BEATS`): the outcome act starts at beat 61, a full beat before the frame starts closing at 62. Route timing, the window and the judgement are unchanged (only when the act starts). The acting strips now shoot committed at 60.8 and success / failure at 61.8 (`tools/run/capture.sh`, `capture_path.sh`) | `before_acting_*` / `after_acting_*` for `mothership_exit_exam`, `underworld_bouncer`, `warehouse_exit_bouncer`, `gospel_jordan_wilderness_path`, `gospel_jordan_wilderness_fires` |
| `ward.dorm.sleeper` selected act did not show | Two bugs, both general: a scene's own cast line on the person the player has just touched undid the touch (`RunPlay._touched_actor`: a scene cast line on the touched person is skipped and logged `held_by_touch`), and the room's two-bar cheer / wave / group directive overwrote a forced act for good (`StoryCrowd._acted` guards `react`, `wave`, `direct`) | `before/after_acting_ward_dorm_sleeper.jpg` |
| `underworld.court.queen` hidden in the dancers | Her home is now the front of the court (`content/story/maps/underworld.json`, 14.9, 4.0); every person a hotspot or its outcome directs is also drawn a little brighter (`StoryCrowd.STORY_LIT` 1.25) | `before/after_acting_underworld_court_queen.jpg` |
| `ward_late.exit.stare`: five states, one body | Turned to the window, turned to you in doubt, resolve, arms up in wonder (success), a stamp (failure); only acts x09 was already baked in, so no sheet changed (`tools/run/acting_data.py`) | `before/after_acting_ward_late_exit_stare.jpg` |
| Gospel fishermen / family: committed barely differs | With the earlier outcome the success (cheer, collapse in relief) is now on screen in the open frame; the fishermen's selected act is a nod (baked) | `before/after_acting_gospel_galilee_fishermen.jpg`, `..._capernaum_family.jpg` |
| Golgotha: the sky darkens behind the hill, not the people | A map thing may carry `dim_people` (0 to 1): while its piece shows, the room and its people are dimmed by it (`StoryStage.people_gain`, the world context's `swell_gain`); `dark1..3` dim 0.10 / 0.16 / 0.22 (about 0.59 with all three) | `golgotha_beats_10_30_58_before_top_after_bottom.jpg`, `golgotha_beat58_people_before_left_after_right.jpg` |
| The room swell is too subtle | 0.40 of the light on the new room's downbeat, a 1.35 flare one beat in, settled after four beats (was 0.55 rising to 1 over two); it lights the people too. Measured on the Warehouse door walk: the upper picture is 35 % brighter at beats 64.3 to 65 than before, equal at 68 | `swell_warehouse_beats_63-68_before_top_after_bottom.jpg` |
| Ember people small / out of the picture in the dark scenes | The real cause: the good rail walked the camera past the scene's companions (the Keeper, the Spring, the Deep Halls, the Falls, the marsh, the High Pass, the plain, the throat, the Birch Hall, the ford). The rail now stops short and the companions stand ahead of it in a lamp (`tools/story/ember_maps.py`, regenerated maps); the drowned thing is larger and nearer the bridge | `before/after_ember_keeper_*`, `before/after_ember_spring_swell_*`, `ember_deep_halls_drowned_*`, `ember_falls_*`, `before/after_ember_companions_*` |
| The Hollow One reads cyan in the marsh | A warm lamp (`lt_ho_m`) on the pair | in `after_ember_companions_*` (first row) |
| Squadron C03 to C06: the camera looks at a wall or the ceiling in the window | The rail's glance in the hotspot window (the last block) never pitches and turns at most 8 degrees, and its in-room walk does not turn (`RunRail.WINDOW_GLANCE_DEG`; every world) | `before_squadron_route_*.jpg` / `after_squadron_c03_c04_c05_c06_c12_c02_beats_44_54.jpg` |
| C02's loud orange berm, C12's bright coast | The flight line's light 0.85 to 0.72 and a cooler tint; the coast 0.95 to 0.78 | same strips |
| Pieces nobody looked at | `swell` (the Spring) reads as a big white flare at beat 51; `drowned` now reads between Bram and the Warden; `rider_shadow` was off the picture (moved beside the hearth, now a clear rider on the wall at beats 50 and 56); `long_shadow` is still not visible on the dark floor (see below) | `after_piece_rider_shadow_*`, `after_ember_spring_swell_*`, `ember_deep_halls_drowned_*`, `after_ember_keeper_*` |
| Plan D10: a finished path's portal | `look.finished` on a hotspot: `{flags_any, available, tint}`; the three Warehouse portals carry their path's ending flags (`keep:path_<id>_<ending>`, read from each path's run.json by `make_hotspots.py`) and the new look `crown` (a gold ring with three motes circling the portal). Validated by `HotspotContract._validate_finished` and, for portals, by `RunData._check_portal`. The home screen already lists a path's reached worlds under Start from a reached level (`src/run/run_levels.gd`) | `d10_portal_radio_beat54_plain_left_finished_right.png`, `d10_portal_radio_beats_50_54_plain_top_finished_bottom.jpg` |
| Screenshot aid | The hotspot view now draws from the screenshot camera (`RW_STORY_CAM`), so a framed shot shows rings, not edge beacons (play is unchanged) | the D10 shots |

Checks after the pass: `bash tools/test.sh` **74,354 checks, 0 failures**, the Python content tests OK; `check_hotspots.py` 0 errors (main, gospel, squadron, ember; warnings as before). New tests: the half-beat flash for a scene that is left (`test_run_cast.gd`), the bigger swell and the people taking it (`test_run_hud_silent.gd`), Golgotha dimming the people (`test_gospel.gd`), the window glance (`test_run_rail.gd`), the finished portal look and its validator (`test_run_paths.gd`).

**What still looks weak** (the leftovers were taken up in A13)
* Faces at half size (A4 item: relief / grief / laugh on greys and skeletons, the cyclops's anger / doubt / shame, insect mandibles, `kneel`, hands to the face): not touched. It needs rig work in `tools/story/art/people.py` and a re-bake of the mothership and underworld sheets; left for a pass with the sheet budget in hand.
* `long_shadow` in the Keeper's cavern is still invisible on the dark floor (a translucent piece on a near-black texture); it needs art or a lighter blend.
* C12: the day coast still shows through the quay's gap (dimmer now, not gone); the boat is still a dark hulk. The portal could be closed by a gate thing.
* Many Gospel crowd scenes have directed people at 35 to 60 degrees from the rail's view (wide crowd views; their shots read, but a tool check would flag them). The Ember scenes `marsh.wall`, `marsh.stair` and `mountain.taken` still walk past their companion.
* The queen's committed and success acts (a stare and a nod) still look alike; the Warehouse booth radio is an edge beacon at beats 50 to 54 under perfect play (discoverability, A6 question 5).
* The acting strips in `docs/shots/acting/` were not all re-shot: only the hotspots above (in `docs/shots/polish/`).

**Only the owner's eyes on a phone can judge**: whether the half-beat flash and the outcome at beat 61 read in motion before the frame closes; whether the 1.35 swell flare is "somewhere new" or a flicker; the Golgotha darkness on a phone screen in daylight; the crown look at phone size; the brighter directed people (do they look lit or pasted on).

## A10. Audio polish (5 November 2026, after Stage 6)

The owner's brief: *the bass is not prominent enough, and some songs or phases do not sit with the player long enough.* An agent cannot listen, so everything below was **measured**, made **data**, and every call made on the owner's behalf has a one-line
revert. Nothing in gameplay changed: judgement, energy, tap windows, cue families, charts, the reveal beat, the route window and the phase length are as they were (the 174 run's timing is untouched; the walks and the matrix still pass).
The owner's Squadron WAVs and all MIDI are untouched on disk; the only audio files rewritten are the Gospel and Ember placeholders' bass stems (synthesised, see 4).

### 1. The measuring tool

`python tools/run/measure_mix.py [--run main|gospel|squadron|ember] [--out x.md] [--json x.json] [--before old.json] [--root other checkout]` renders every scene's 64-beat phase offline from the packs the way `RunAudio` plays it under perfect play (stage table, reveal on beat 16,
arrangement sections and recipes, the bass bus, the run level, the carry) and reports per scene: seconds each voice is audible and the block it enters, seconds the bass leads, LUFS (BS.1770), the sample peak, BASS PROMINENCE (30-250 Hz and 30-80 Hz share of the mix
with the bass in), bass minus drums and minus synth (dB), PHONE BASS (the bass's 150-1000 Hz energy against the mix's 150-8000 Hz: what a phone speaker can play), and a dwell table per run. The bass bus model was checked against Godot itself: in a real recording
`check_run_audio.py` (which now fits the bass as it leaves the bus) explains 99.5 to 100 % of every block on the stub and on Squadron C08 and C10, and 96 % on C05 (its heavy setting: the model reads Godot's bass about 0.8 dB low there).
Results: `docs/shots/audio/mix_before.md` (origin/main 710a96a5, measured with the same tool on an extracted copy) and `docs/shots/audio/mix_after.md` (with the before/after table at the top; both also as JSON).

### 2. What the measurements said (before)

| | main run (174) | Gospel (124) | Squadron (140) | Ember (145) |
| --- | --- | --- | --- | --- |
| phase / block | 22.1 s / 5.5 s | 31.0 / 7.7 s | 27.4 / 6.9 s | 26.5 / 6.6 s |
| how long one song stays | a world's family: 4, 4 and 8 phases along the default route (88 to 177 s), but **two 8-bar sections per phase: the arrangement turns over every 11 s** | **one phase per loop (31 s)** | **one phase per loop (27 s)** | **one phase per loop (26.5 s)** |
| bass audible / leading per phase | 16.6 s / **11.6 s** | 23.2 / 23.2 s | 20.6 / 19.6 s | 19.9 / 19.9 s |
| bass minus drums | **+3.9 dB** | +10.0 | +11.0 (C05 **-1.3**, C06 **+1.8**) | +12.0 |
| LUFS / worst peak | **-20.7** / -2.8 dBFS | -12.6 / **+1.0** | -14.3 / -0.5 | -12.6 / **+0.2** |

The 174 run was the weak one: stage 2 ("drums return") cut the bass to 0.5, the arrangement recipes cut it again (`fragile` and `intro` 0.7: the Hospital's bass sat at 0.35 for a whole block), every scene change dropped the bass for the 16-beat drums-alone block
(5.5 s of every 22 s), 24 hotspots dipped the bass 9 dB for 8 beats at the end of the strongest block, and the whole run was 6 to 8 LU quieter than the paths (a jump at every portal). The paths were already bass-led; Gospel and Ember clipped (+1.0 and +0.2 dBFS);
Squadron C05/C06 had the bass under the drums.

### 3. What changed (all data; the revert is the old value)

| Decision | Where | Value now | Revert to |
| --- | --- | --- | --- |
| Stage 2 keeps the bass in (no strip-back while the drums return) | `content/run/run.json` `stages[2].gains.bass` (Gospel, Ember, stub inherit; Squadron has its own 0.9) | 0.85 | 0.5 |
| The synth sits a little under the bass in the strongest block | `stages[3].gains.other` | 0.5 | 0.6 |
| A recipe never takes the bass under 0.9 in the run (recipes themselves untouched: the chapters' renders use them) | `mix.recipe_bass_floor` | 0.9 | 0 |
| **The bass carries over a scene change inside one music family** (same world: same key and sound): the old scene's bass plays on at half gain under the new scene's drums-alone block and fades as the new bass enters on beat 16. Never across a world change, a path handoff or a phase without a reveal | `mix.carry_bass` | `{gain 0.5, beats 16}` (31 of 36 main scenes carry; paths: every scene is its own loop, so none) | `gain: 0` |
| A gentler hotspot dip | `mix.dip_gain`, `mix.dip_beats` | 0.55 (-5.2 dB) for 6 beats | 0.35 for 8 |
| The bass bus (`RunBassToneA/B`, bass voice only, before the treatment): high-pass, low shelf, Godot WAVESHAPE drive with pre and post gain: harmonics a phone speaker plays, body lifted, peaks rounded | `mix.bass_bus` (main) | HP 30 Hz, shelf +2 dB at 110 Hz, drive 0.6, pre +6, post -9 dB | `enabled: false` |
| per path | `content/paths/<id>/run.json` `mix.bass_bus` (merged key by key over the main run's) | Gospel and Ember: HP 25, no shelf, drive 0.4, post -2; Squadron: no HP (the sub stays), drive 0.4, pre +3, post -4 | remove the path's `mix` |
| per scene (Squadron) | `content/paths/squadron/music.json` `bass_bus` | C05, C06: shelf +4 dB at 80 Hz, drive 0.6, pre +10, post -8 / -9 (lifts the quiet body under the transient); C03, C09, C11: shelf +4 dB at 80 Hz (weight for the mid-heavy basses) | remove the scene's `bass_bus` |
| The run's level on the new `RunMix` bus (a plain bus volume: linear, no delay) | `mix.gain_db` | main +2, Gospel -3, Squadron -1.5, Ember -2 dB | 0 |
| Placeholder bass re-synthesised (Gospel house, Ember psytrance; MIDI, charts, drums and pads byte-identical; deterministic) | `tools/content/make_path_placeholders.py` `BASS_VOICES`, then `make_path_placeholders.py gospel|ember --force` | sub sine + saturated mid layer (partials under 150 Hz kept light), psytrance notes plucked (a clear sixteenth pulse); the bass stem's 150-1000 Hz share 0.22 -> 0.34 (Gospel), 0.19 -> 0.35 (Ember), sub share still 47 to 66 % | `git revert` the regenerated-packs commit (+7.7 MiB of git: 6 unique new blobs) |

The path generators (`make_gospel.py`, `make_ember.py`, `make_squadron.py`, `make_path_placeholders.py`) keep `mix` and each scene's `bass_bus` when they rewrite their files. `beatshaper.py apply` (an owner's import) writes a fresh music.json entry, so
a scene-level `bass_bus` is dropped when its loop is replaced: re-measure with `measure_mix.py --run <path>` and set it again if needed. No limiter: a hard limiter would add a look-ahead delay to the whole run, so the peaks are held by data and
`tools/content/test_mix_polish.py` fails if any scene of any run renders over -0.5 dBFS.

### 4. After (`docs/shots/audio/mix_after.md`)

| run | bass minus drums | bass leads s / phase | bass audible s / phase | phone bass | LUFS | worst peak |
| --- | --- | --- | --- | --- | --- | --- |
| main | +3.9 -> **+9.3 dB** | 11.6 -> **20.2 of 22.1** | 16.6 -> **21.3** (the carry) | -2.9 -> -1.3 dB | -20.7 -> **-14.8** | -2.8 -> -1.1 dBFS |
| Gospel | +10.0 -> +12.0 | 23.2 -> 23.2 of 31.0 | 23.2 | -0.2 -> -0.2 | -12.6 -> -14.1 | +1.0 -> **-0.8** |
| Squadron | +11.0 -> +14.4 (C05 -1.3 -> **+9.1**, C06 +1.8 -> **+10.4**) | 19.6 -> 20.6 of 27.4 | 20.6 | -1.2 -> -0.6 (C05 -5.0 -> -1.2) | -14.3 -> -12.9 | -0.5 -> -0.9 |
| Ember | +12.0 -> +13.3 | 19.9 -> 19.9 of 26.5 | 19.9 | -0.2 -> -0.1 | -12.6 -> -13.1 | +0.2 -> **-1.3** |

The four runs now sit within 2 LU of each other (they were 8 apart), so a portal no longer jumps in level. Ember's sub share of the whole mix fell (52 -> 44 %) because its new bass puts more energy where a phone can hear it; Squadron's thin-sub scenes gained a little
(C11 10 -> 17 %). Recordings (dummy driver): `docs/shots/audio/handoff_check_after.txt` (balcony star -> stub -> Warehouse: every block fitted, 99.2 to 99.5 % explained, handoffs +2.2 ms in and -6.5 ms out, in-path boundary -6.1 ms, delay spread 12.6 ms:
the same numbers as before the polish, so no regression in the grid; `RESULT CHECK` only because the stub's spread is over the script's 6 ms, as it was before) and `docs/shots/audio/squadron_check_after.txt` (C05, C08, C10: every block ok, boundaries +9.1 ms against the
29.4 ms floor; spread 18.3 ms on a loaded machine).

### 5. Not done: it would change gameplay (recommendations for the owner)

1. **A second lap for the paths' loops** (built afterwards: A12). Gospel, Squadron and Ember play each loop for exactly one phase (26 to 31 s) and then the scene, and so the song, changes. Letting a scene play two phases (a `laps: 2`, the route window only in the second) would double each song's
   time with the player, but it doubles the blocks judged per scene (energy), moves every hotspot window and cast line, and breaks the 2 to 4 hotspot rule's pacing: the owner's call.
2. **Bass in the first scene of a world's drums-alone block.** The carry fills block 0 after the first scene; at a world entry the block stays drums alone, because a bass started before the reveal would move the bass phrase (and the bass cues) off the reveal beat.
3. **Fewer turnovers in the 174 run.** Most scenes play two 8-bar sections (a pack and a mix recipe change every 11 s). One 16-bar section per scene would hold one arrangement for the whole phase, but the second section's chart changes the cues of blocks 3 and 4: an
   `arrange.py generate` option, and a gameplay change.
4. **Squadron C05/C06** would gain most from a re-export with the bass transient tamed (the bus lifts the body; it cannot restore what the source lacks), and 8-bar loops would halve how often the loop repeats inside a phase.

### 6. What only the owner's ears can judge (listen for these)

1. **The carry, Warehouse floor -> bar (and every in-world door walk):** the floor's bass at half level under the bar's drums-alone block, then the bar's own bass on beat 16. Seamless, or a muddy overlap where the two bass lines differ? (`carry_bass.gain` 0 turns it off.)
2. **The 174 bass's saturation on earbuds and on the phone speaker** (drive 0.6 with +6 dB in): audible on the phone speaker now, but is it fuzzy on the Underworld and Ward reese basses? (lower `drive` or `pre_gain_db`; raise `gain_db` to keep the level).
3. **Squadron C05 and C06:** the body under the transient is lifted ~9 dB; does the hit still punch, or does it sound squashed? (their `bass_bus` in squadron music.json).
4. **Drum blocks still readable:** in stage 2 the bass is now at 0.85 under the drum cues (was 0.5). Can the player still hear the kick and snare they tap? (`stages[2].gains.bass`).
5. **Levels at the portals and the new placeholder bass:** the main run is ~6 LU louder than before and now level with the paths; the Gospel house and Ember psytrance bass were re-synthesised (sub + saturated mid, plucked sixteenths). Too loud, too buzzy, or right?

---

## A11. Debug / Playtest mode (5 November 2026)

The owner's brief: *a debug mode where I can simply choose each musical / visual scene, with the audio used clearly identified, so if I don't like a passage it is easy to identify which songs or visuals I don't like.*
Built (`docs/DEBUG_MODE.md` is the manual): the home screen's **Debug / Playtest** button opens a scrollable list of all 82 scenes (the 174 run's 36, Gospel 17, Squadron 14, Ember 15; the stub only outside exports); a row starts the
game AT the scene through the run's own start machinery; **Info** shows the pack ids, the stem files named as the owner's exports (from `pack.json`), OWNER / PLACEHOLDER / temporary from `music.json`, the MIDI the cues come from,
the mix in force and the visual ids (map, view, light preset, pieces, cast, crowd, hotspots); an in-play overlay (debug only) shows the same live with the phase and block clock, and three feedback buttons (keys M, V, L)
append to `user://playtest_notes.md` and `.jsonl`; a notes screen with Copy all; `tools/run/playtest_notes_summary.py` ranks the disliked songs and visuals. Pause shows Back to scene list.
Decisions made: the list plays in a **throwaway save** (the owner's reached levels are never touched); **every 174-run scene has three arrangements and the game picks one by the per-run seed**, so the list has an arrangement option
(`RunData.arrangement_override`, default off: the game's own pick) and the notes record the arrangement that played; the autoplay assist is the existing `RW_RUN_BOT=perfect`; no gameplay changed. Code in `src/debug/`, tests
`tests/test_playtest.gd`, shots `docs/shots/debug/` (`tools/run/shoot_debug.sh`). Not run on a phone.

## A12. Two laps per path scene (5 November 2026)

The owner approved the fix A10 section 5 item 1 recommended: *the three paths' songs did not sit with the player long enough* (a scene, and so its song, lasted one 64-beat phase: Gospel 31.0 s, Squadron 27.4 s, Ember 26.5 s), so **a scene of a path now plays its music and staging for two consecutive phases ("laps") before the route commits**. The 174 BPM main run keeps one and is untouched.
Everything is data plus a small engine change; the full description is `docs/CONTINUOUS_RUN.md` "Two laps per path scene". Nobody has played or heard it: it was built and measured on the virtual clock with the dummy audio driver.

### 1. What it is, in one screen

| | |
| --- | --- |
| **Data** | `path.laps` in a path's `run.json` (the default of its scenes) and `laps` on a scene (wins); 1 to 4; only paths may exceed 1. Shipped: `path.laps` 2 in `gospel`, `squadron`, `ember`. `RunData.laps_of(id)`; `check_path.gd` and `check_hotspots.py` validate it |
| **Single-lap scenes** | **J00 `jordan`** (the prologue: a night road with one way on; a minute of it before the first story scene would be a wait), **J14 `jerusalem.golgotha`** (the sky darkens a step a block and a witness or a soldier steps forward a block: one descent, authored for one pass; a second lap would only repeat it), **E00 `hollow`** (the orchard prologue, one way on). `stub` stays 1. Squadron has no exception (its first scene has two ways on). **The endings take two laps** (J15, J16, C13, E12, E13): the finale is where the player most wants to sit in the song, and the ending's `keep:` flag is still set by its default exit at the end of the last lap |
| **Lap 1** | the scene's full phase by the stage table (drums, bass, drums back, bass strongest) with **no hotspot window, no route window, no commit, no riser or fall**: `choose()` is refused and `shown()` is empty |
| **The boundary** | the stage of lap 2's first block is the stage of lap 1's last block, one step on after a pass (a perfect player: stages 0 1 2 3 \| 3 3 3 3). **Nothing is stripped back and no voice restarts** (RunAudio schedules nothing for a lap; every loop tiles a lap). A player who earned nothing in lap 1 starts lap 2 on drums alone and the table brings the bass in again: a second chance, never a harsher one. A perfect scene's cue families: drums, bass, drums, bass, **bass x 4** |
| **Lap 2** | the phase as it always was: hotspots (2 to 4, **lap 2 only**), the 16-beat route window at beat 48 (riser if the strongest stage is in), the commit at beat 60.5, the route lock, the door walk (beat 61), the passage frame (beats 62 to 64), the tempo handoff, the flags. No timing of them moved |
| **Cast** | `at_beat` counts from the scene's first downbeat over both laps (validator: 0 to 64 x laps - 1). Re-timed by `tools/run/laps.py` inside the three generators (their tables still author one phase): a line before beat 48 is spread (b x 2; a hold of 12 beats or more holds twice as long), a line from beat 48 on keeps its place in the last lap (b + 64), so every reaction to the commit still lands at beats 125 to 127. No line added, so no text. `block_fx` entries take an optional `lap` (default 1) |
| **Staging** | lamps, set pieces, rail, people and `lights_*` are not reset at the boundary (no room swell, no pieces reset). The rail keeps stepping |
| **Pause menu** | "Leave this path" now also ends the scene at the end of a lap before the last |
| **Debug mode** | the scene list shows `x2`; the overlay reads `lap 2 of 2 \| block k/4 \| ... beat 70.0/128 of the scene (6.0 of the lap)`; Info says "2 laps of 64 beats"; the notes carry `lap` and `laps` (`docs/DEBUG_MODE.md`) |
| **Counting** | `phase_n` counts laps and `scene_index()` scenes; the result screen, the save's best phases, the scripted bots' routes and `RW_RUN_UNTIL_PHASE` count scenes. The audio's two bus pairs still alternate per scene |

### 2. Dwell, before and after (`docs/shots/audio/mix_laps_before.md` with `measure_mix.py --force-laps 1`, and `mix_laps_after.md`; the same render and tool, perfect play)

| path | a two-lap scene lasts | default route (12 or 13 scenes) | bass audible in a two-lap scene | bass leads | mean LUFS | worst peak | bass minus drums |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gospel (124 BPM) | 31.0 -> **61.9 s** | 372 -> **681 s** | 23.2 -> **54.2 s** (75 -> 88 % of the scene) | same as audible | -14.1 -> -13.6 | -0.8 -> -0.8 dBFS | +12.0 -> +13.9 dB |
| Squadron (140) | 27.4 -> **54.9 s** | 329 -> **658 s** | 20.6 -> **48.0 s** (75 -> 87 %) | same | -12.9 -> -12.6 | -0.9 -> -0.9 | +14.4 -> +16.0 |
| Ember (145) | 26.5 -> **53.0 s** | 344 -> **662 s** | 19.9 -> **46.3 s** (75 -> 87 %) | same | -13.1 -> -12.6 | -1.3 -> -1.3 | +13.3 -> +15.4 |

(A one-lap scene keeps its old numbers.) The level rises about half a LU because the second lap is all at the strongest stage (drums 0.4, bass 1.0, synth 0.5); no peak moved, `tools/content/test_mix_polish.py` still passes. A song's loop now repeats: Gospel and Ember 8-bar loops 4 times in a scene, **Squadron's 4-bar loops 8 times in 55 s** (7 s each).
Real-time check (dummy driver): see section 5.

### 3. The energy economy (not retuned; `tools/run/laps_energy.gd`, `RW_MATRIX_LAPS=1` on the matrix)

Judgement windows, the pass credit and the energy gain and loss of a block are exactly the single phase's (asserted against the formula in `tests/test_run_laps.gd`), and so is a hotspot outcome's energy; but a scene now has 8 blocks to survive and one commit per 8 blocks instead of 4. `tools/run/laps_energy.gd` plays each path with scripted players of a given cue accuracy over 24 seeds, default exits:

| accuracy | Gospel reaches an ending (one lap -> two) | Ember | Squadron |
| --- | --- | --- | --- |
| 0.50 | 0/24 -> 0/24 (dies after 6.4 -> 4.4 scenes, 24 -> 27 blocks) | 0/24 -> 0/24 | never (the default exits loop) |
| 0.55 | **16/24 -> 7/24** | **15/24 -> 11/24** | survives 270 -> 190 blocks before the loop's 3000 s cap |
| 0.60 and up | 24/24 -> 24/24, lowest crowd energy the same (29.7 at 0.6, 49 at 0.7), mean energy 81 -> 85 | same (34.8; 82 -> 87) | 0.60: a seed or two now dies (437 -> 421 blocks of 437); 0.70 and up reach the cap either way |

So a player who hits more than about 60 % of the cues feels no difference; a marginal one (about 55 %) loses the floor in the longer scene noticeably more often, and a 50 % player dies about as many blocks in, but in an earlier scene. The matrix (`tests/test_run_matrix.gd`: perfect, 0.8, sloppy, none; every tap policy) is unchanged for perfect, 0.8 and sloppy (they end at 100 energy); a player who never touches the pads now dies in Squadron's first scene instead of its second. **Not retuned, as asked**; if it is too harsh for the 55 % player, the knobs are `energy.fail_loss` / `pass_gain` in `run.json` (they also move the main run), or `laps` back to 1.

### 4. What was verified (this PC, 5 November 2026, Godot 4.5.1 console, Windows 11)

* `bash tools/test.sh` (the whole project, exit code 0): **80,754 checks, 0 failures** in the Godot suite (was 74,354 after A9) and the Python content tests OK (208; they were 181); the Godot suite grew by `tests/test_run_laps.gd` (19 tests, about 2,100 checks: the shipped laps, the validator, the window and commit in the last lap only, the stage and cue families across the boundary, the bass phrase on the loop's own grid in all three paths, a missed block and a late reveal, the energy per block against the formula, the cast across laps at any frame step and across a stall, leaving in lap 1, the handoff after two laps and the Warehouse grid, the main run without laps, the audio voices across the boundary, the real scene's two laps with the hotspots in the second only, the pause menu's leave in lap 1, the debug mode) and `tools/content/test_laps.py` (9). Existing tests that assumed a path scene was one phase were changed to count scenes (`test_run_matrix`, `test_run_ember`, `test_gospel`, `test_playtest`); no main-run test was changed and all pass.
* `python3 tools/run/check_hotspots.py --path gospel|squadron|ember|stub` and the main run: 0 errors (the laps and every cast range are checked); `check_path.gd` 0 errors for all four.
* `GODOT=<console> bash tools/run/walk_run.sh --path gospel|squadron|ember` (real scenes, virtual clock, isolated save, dummy audio; the walk's own check now also compares the sequence of `lap_start`s with the data): all three `run walk-through: OK`: gospel 7 walks (`perfect`, `sloppy`, `none`, `road_end`, `branch_a`, `branch_b`, `branch_c`) **17 of 17 scenes**, squadron 5 walks (`perfect`, `sloppy`, `none`, `loop`, `clause`) **14 of 14**, ember 6 walks (`perfect`, `sloppy`, `none`, `kept`, `taken`, `lantern`) **15 of 15**; a perfect Gospel walk from the star to the tomb and back to the Warehouse is 681 s of song time.
* **Real-time recordings** (`tools/story/record_music.gd`, dummy audio driver, perfect play, then `tools/story/check_run_audio.py`, which now fits both laps and reports each lap boundary): Squadron `air.c05` (85 s), Gospel `jordan.baptism` (72 s), Ember `north` (66 s), all `RESULT ok` (`docs/shots/audio/laps_check_{squadron,gospel,ember}.txt`): the eight blocks of the scene fit their stage gains (96 to 100 % explained; the bass fitted at its full gain through lap 2: no strip-back), **the drums' delay 8 beats before and 8 beats after the lap boundary is the same to 0.00 ms** (the beat grid goes on without a jump), **no voice was started at the boundary**, the delay is the same in the whole scene (spread 0.00 ms) and the recorded tempo equals the engine's (124.000, 140.000, 145.000 BPM).
* `python tools/run/measure_mix.py` (before: `--force-laps 1`): section 2.
* `tools/run/laps_energy.gd`: section 3 (`docs/shots/audio/laps_energy.txt`).

### 5. What could not be verified

* **Nobody has listened to it or played it by hand, and nothing ran on a phone.** The feel of the longer scene, the bass across the boundary and the hotspots arriving after a minute are the owner's.
* The dummy audio driver has no output latency; the recording check proves the grid and the voices, not the sound. The recordings stop shortly after the first scene's second lap, so the scene change after a two-lap scene (the ordinary phase change, unchanged) was not re-recorded; the tempo handoff after two laps is proven by the engine test (the handoff on the 128th beat, the Warehouse's cues on the 174 grid) and not by a recording.
* The Squadron loops were not re-exported: 4-bar loops repeat 8 times per scene.

### 6. What only the owner's ears and phone can judge

1. **Does it drag?** A minute in one room on one loop (Squadron: a 7-second loop eight times) before the choice: does lap 2 feel earned, or like a wait? If it drags, set that path's `laps` back to 1 (one value) or a single scene's `"laps": 1`.
2. **Does the bass hold across the boundary?** At the downbeat of lap 2 nothing should change except the cue pattern (bass cues for four blocks in a row); no dropout, no restart of the loop, no gap in the groove. Listen at the J01 / C01 / E01 boundaries on a phone speaker and on earbuds.
3. **Four blocks of bass cues in a row** (lap 2, perfect play): is it a pleasure ("enjoy the bass") or tiring? An alternative is a drums-cue block inside lap 2 (the stage table is data, but this needs a lap-2 stage rule in the engine: not built).
4. **Hotspots only after a minute:** do people notice the doors and people in lap 2, or do they stop looking in lap 1? Do the people's acts spread over 128 beats (stretched story beats, the reactions at the end) still read?
5. **The cast stretched over two laps:** a person holding an act for 24 or 32 beats (a stare, a kneel) between story beats: patient or frozen?
6. **The energy for a weaker player** (section 3): does the 55 % player lose the crowd too soon in a longer scene?
7. **The pause menu's "Leave this path"** now ends the scene at the end of lap 1 as well: the passage frame closing at the end of the first lap should look like any other exit.

### 7. How to revert

* All three paths: `path.laps` to 1 in `content/paths/gospel|squadron|ember/run.json` (or `LAPS = 1` in the generator and re-run it: `python3 tools/content/make_gospel.py --run-only`, `python3 tools/paths/make_squadron.py`, `python3 tools/run/make_ember.py`; the cast goes back to its authored beats). One path: that path's value. One scene: `"laps": 1` on it. Nothing else changes; the tests and walks follow the data. Gospel / Ember / Squadron's old `run.json` is also in `git show 55f6cd3f:content/paths/<id>/run.json`.
* The engine can stay: with every `laps` 1 it is the old engine (the main run's 36 scenes never reach any lap code).

## A13. Visual polish 2 (5 November 2026): the leftovers of A9

Branch `feature/polish-leftovers` (cut from origin/main 55f6cd3f), done from stills on the virtual clock; every picture below was looked at before and after. Pairs are in `docs/shots/polish2/`.

| A9 "not fixed" item | What changed | Proof (`docs/shots/polish2/`) |
| --- | --- | --- |
| Faces at half size alike (relief / grief / laugh on greys and skeletons, the cyclops's anger / doubt / shame, insect mandibles) | New module `tools/story/art/half_faces.py`: a small hand-drawn picture per face for the four species whose heads are 5 to 9 pixels wide at the half size (grey, cyclops, insect, skeleton: all 14 faces), and for the full-size insect and skeleton (11 pixels wide) and the grey's relief / grief / laugh. Each face differs from every other in the eye's shape (round, slanted, closed line, drooping diagonal), the brow, a tear column, an open mouth or dropped jaw, the teeth or the mandibles (now dark pincers that open, clamp, droop or cross). `Painter.half_face` draws them as the face decal (the three-quarter turn shifts the picture and closes up its far half). The grey's fear / awe mouths at full size differ too (`act_grey`). Other species and the humans are untouched | `faces_half_size_before_above_after_below.jpg`, `faces_full_size_before_above_after_below.jpg` (14 faces; the half-size strip is shown 9x, the full-size one 5x) |
| `kneel` read as a kneel-sit, `cover_face` / `collapse` hands never reached the face | `Body._one_knee_down`: the hip sinks a thigh's length, one knee is on the floor under it with the shin gone back (the foot lifted, or lying behind in the three-quarter view), the other thigh goes out (forward in the three-quarter view) with its shin straight down. `Body._hands_to_face`: for the front and three-quarter facings the hands go to the face (elbow solved from the hand, out and low), and `Painter.arm` draws them as wide palms with finger gaps in front of the head, so the face (and its grief) is hidden. Back views are unchanged | `kneel_cover_face_collapse_before_top_after_bottom.jpg` (underworld punk and brute, mothership alien) |
| Ember `marsh.wall`, `marsh.stair`, `mountain.taken`: the rail walks past the companion | The rails stop short (`wall_mid`/`wall_near`, `stair_mid`/`stair_fwd`, `camp_mid`/`camp_fwd`; the Hollow One of the stair and Bram of the camp stand a little further on) | `ember_marsh_wall_beats_10_30_52_...`, `ember_marsh_stair_beats_10_30_52_...`, `ember_mountain_taken_beats_10_30_52_before_top_after_bottom.jpg` (the companion, the Hollow One or Bram, now stays in the picture; the stair's people are small because the rail stops about 5 m short) |
| `long_shadow` invisible on the dark floor | The piece is now a pool of the altar's light on the floor with the shadow cut out of it as a near-black wedge and a bright rim along its edge (`pc_long_shadow`), and it lies across the floor between the pair and the altar, 9 m wide (it lay 2 m in front of the rail's camera, under its feet: that, more than the colour, was why it was never seen). It is a flat decal, so from the rail's grazing eye height it reads as a warm lit pool with a dark band, not as the figure's silhouette | `ember_keeper_long_shadow_beats_38_50_58_before_top_after_bottom.jpg` (visible at 38 and 50; at 58 the rail has moved on and the pool is out of the picture) |
| C12 quay: the bright day coast, the dark boat | The bright block was not the gap: the coast's own west wall (`wall_dunes`, 4.5 m) lies in the quay's east wall's plane and is drawn over it (walls are not back-face culled). The coast's west wall is now `wall_quay` (the harbour wall's other face), the quay-to-coast portal is a 0.9 m crack of daylight in the far corner (a sector must stay reachable), the boat is bigger, nearer, lighter and lit by a stronger lantern, the fisherman stands beside it | `squadron_c12_quay_beats_30_52_before_top_after_bottom.jpg` |
| Queen's committed and success acts alike | Committed: she points at you, sternly (`point`, `anger`); success: an amused nod (`nod`, `laugh`). Both acts and faces are baked for her | `acting/underworld_court_queen.jpg` |
| Stale acting strips | Re-shot with `capture.sh --acting` and `capture_path.sh <path> --acting` for the main run, the Gospel, the Mission Count and Ember; contact sheets rebuilt | `docs/shots/acting/` |

**Sheet bytes** (people pages, before -> after, from origin/main): night_one 3,555,788 -> 3,553,613; mothership 9,645,545 -> 9,658,359 (+0.13 %); underworld 9,236,297 -> 9,245,310 (+0.10 %); hospital 8,963,276 -> 8,961,056; mental_hospital 10,056,393 -> 10,050,469; the path maps within +-1.5 % (ash_land +0.16 %, deep_halls -1.46 %). Nothing is near the +15 % budget; the pictures are flat colour, so they compress like the old faces. The sheets are a separate commit from the code.

**Tests**: `tools/content/test_faces_lod2.py` (unittest, run by `tools/test.sh`): every one of the 14 faces of a grey, a cyclops, an insect and a skeleton differs from every other by at least 5 pixels at the half size in front view (3 in the three-quarter view; 3 at full size for the ten acted faces), the owner's listed pairs by at least 6 at both sizes, every picture is well formed, `kneel` has one knee on the floor and the other up in all three facings, the hands of `cover_face` and `collapse` are over the face in front and three-quarter, and two different faces of a person covering theirs are the same picture.

**Rebuild**: `python3 tools/story/build_assets.py <chapter> people` (five chapters), `build_assets.py airfield|city|harbour`, `build_ember.py people`, `build_gospel_art.py --people`, then `godot --headless --path . --import`; `build_gospel_art.py` also rewrites its map and story JSON with CRLF line ends on Windows: restore those with `git checkout`.

**What remains weak**
* The picture faces are 5 to 9 pixels wide; they differ, but a grey's relief and shame, or an insect's neutral and doubt, differ by only 5 to 8 pixels at half size, and in the three-quarter view some pairs by 3. Only a phone will say whether the eye resolves them at the real distance.
* The cyclops at full size is untouched (its pairs were already 10 or more pixels apart); the humanoid aliens, blobs, demons and humans have no half-size picture faces (blobs' neutral / happy / cheer / sad are still identical at half size).
* `kneel`: the planted knee is large on the front view (the thigh comes towards the camera); long skirts and gowns hide the whole leg pose. `cover_face`: the hands cover the whole face (the grief face cannot be seen, by design); the elbows are wide and at shoulder height, so the sleeves make a wing shape on a long-sleeved person.
* The C12 crack of daylight is a thin strip of bright coast (a tease, and a bright pixel column on a dark quay). The wall z-fighting (coplanar walls of two sectors, no back-face culling) probably affects other maps with adjacent rooms; not audited.

**Only the owner's eyes on a phone can judge**: whether the half-size faces read at the distance the crowd is seen from; whether the one-knee kneel and the hands over the face read in motion (the frames cycle through the pose); whether the long shadow's lit pool reads as a shadow cast by a figure or as a glowing floor patch; whether the Ember rails now feel right (the camera stops about four metres short of the companions).

## A14. Choice clarity (5 November 2026, branch `feature/choice-clarity`)

The owner's brief: *every branching choice must be clear in the world: people and things show the options, the default, the current choice and how a touch changes it; not just lights.* **Read `docs/CHOICE_CLARITY.md`.**
* Audit: of 82 run scenes 2 were clear, 28 unclear (options only as light on a doorway point or an empty spot), 52 had an option the player cannot see in the window (an edge beacon); no scene showed the current choice except by a brighter ring. The Bassment's 27 branching passages were all unclear.
* Built: a CURRENT choice (the touched option, else the default) staged in the world from the scene's first beat: people beckon happy (current) or plead sad (other), exits are drawn doors (open with a round green lamp / shut with a square red one), signs outdoors or boards across a doorway thing, the wizard happy or bowed, objects bob and light; data `staging` blocks with `states` steps (pieces, people, frames, props, lamps) for the bespoke briefs. Touch rules, windows, the commit and outcomes are unchanged.
* Pilot strips `docs/shots/choice/` (Warehouse floor/bar/balcony, Gospel J04, the Mothership door pair, Bassment passage 10); tests `tests/test_choice_clarity.gd`; the per-world remaining work and art briefs are in section 6 of the doc; owner decisions (touch before the window, the window camera) in section 7.
* Status and the numbered pickup list (done / partly / not started, the author API, phone checks): section 0 of the doc. First pickup: the window camera (E1).
* Rebase note: the people sheets of all 16 maps were re-baked for the choice acts; after merging another branch that re-bakes people, re-bake each map's people (`build_assets.py <chapter> people` for the Story chapters and airfield / city / harbour, `build_ember.py people`, `build_gospel_art.py --people`; do NOT give the Ember or Gospel map names to `build_assets.py`, it would silently rebuild Night One; the bake reads `staging` from the data). Done after the merge into main (see `docs/PICKUP.md`).


## A15. Look pass merged with choice clarity (5 November 2026, branch `integrate/look-pass`)

`origin/feature/look-pass` (paused, 4 commits on an old main) was merged into main's tip. It is a visual branch: no music, stem, pack, assignment or debug-listing file differs from `origin/main` (`git diff --stat` over `songs`, `content/library`, `content/music`, `content/paths`, `content/run`, `assets/audio`, `src/audio`, `src/debug`: empty). What it brings: the Bassment's `wall_echo` and `wall_burrow` textures, the hotspot light language and edge beacons, the camera that faces the window (the "window camera" of A14's pickup E1), and the StoryPlayer face-look fix. The pictures were taken from three checkouts, `A` origin/main, `B` the look-pass tip alone (an older base: it has no doors, lamps or paths, and its Gospel and Ember shots are not valid), `C` the merge, all on the virtual clock at 1280 x 720 with the player's own camera, in `docs/shots/lookpass_merge/cmp_*.jpg` (three panels, top to bottom A, B, C).

**Conflicts (3 files).** `docs/TRIAL_OPENING.md`: both sentences kept (main's silent-HUD note, look-pass's rewording of the hotspot language). `tests/test_run_matrix.gd`: main's `start` scene argument and `lap_start` event plus look-pass's `face` switch and window counters; the signature is now `_simulate(policy, seed, data, taps, start, face)` and the window test passes `"warehouse", face`. `src/run/hotspot_view.gd`: not a text merge. The two sides redrew the same function in opposite ways (main: one `_draw_entry`, the choice layer staged inside `_draw`; look-pass: a per-frame layout in `_process` and two passes, additive light plus crisp rings). The result takes look-pass's drawing as the base and ports main onto it: `_process` now runs `choice_snapshot`, `_stage_choice` and `_manage_acting` (before it did so inside `_draw`; they must run whether or not a hotspot is on show, so the choice lets go of the world when it ends); the entries get their `role` from the snapshot; `layout(..., rects)`, `hit` with `touch_rect`, `finished`, `acting`, the choice layer and `refresh_choice` are main's, unchanged. Everything else merged without conflict (`run_journey`, `run_play`, `story_player`, `trial_scene`, `story_data`, the Bassment maps and manifest).

**How the two hotspot languages combine.** A staged option (two or more options staged, `role` set) is lit by its role as main wants (green `CURRENT_COL` when current or committed, red `OTHER_COL` otherwise; the current one is the doubled ring) but drawn in look-pass's shapes: a pool of light on the floor, a thick outlined ring, the ripple on every beat; its selected ring keeps the role colour (pale green) with the circling motes instead of going white; it gets no shaft, glow or slit, because the person or the drawn door shows the state (main's rule, "the light stays on the floor and never covers a face or a door"); other staged options only dim to 75 % (`DIM_STAGED`) while one is selected, so the red still reads. A hotspot with no staged choice (single ways on in the Bassment, objects alone) is look-pass's full language (pool, ring, ripple, shaft with motes, glow, door slit, crack). Edge beacons (look-pass: border leak, half-sun, ring, ripple, motes) take the role colour too. A finished portal keeps its own tint and the `crown` look (ring and three orbiting motes, ported to both passes). High contrast still overrides colour.

**Look verdict per piece** (shots `docs/shots/lookpass_merge/`; I looked at each file):

| Piece | Winner | Why, and where to look |
| --- | --- | --- |
| Bassment textures (`wall_echo`, `wall_burrow`) | look-pass, taken whole | Main's echo chamber is a dark red-mottled wall that merges with the figure and the lit hotspots; look-pass's cold pale ashlar with carved rings makes the round room read as a room and the figure and rings stand out. The warren's warm gnawed earth and brick stair beat main's cold grey-green stone, which reads as any dungeon rather than a rat tunnel, and warm walls make the green and red pools stand out. `cmp_bass_echo.jpg`, `cmp_bass_warren.jpg`; the merged shots keep main's drawn door and green/red lamps on the new walls. The other Bassment zones are unchanged (main's look: the boiler room's red mottle is still the worst; `cmp_bass_boiler_tap.jpg`). |
| Camera faces the window | look-pass, taken whole | Main's options in the window are mostly faint beacons on the border (`cmp_wh_selected.jpg`, `cmp_mship_selected.jpg`, `cmp_gospel_selected.jpg`: panel A); in B and C the head is turned so the exits, people and rings are in the picture. This is A14's missing E1. Caveat: the frame is chosen from the hotspot anchors, not from `door_at`, so a drawn door can be off-centre. |
| Hotspot light language: rings, ripple, pools | look-pass drawing, with main's role colours | Main's ring is a thin 1 to 3 px line that vanishes on a bright floor; look-pass's outlined ring, floor pool and beat ripple read clearly at the same size (`cmp_mship_selected.jpg`, `cmp_bar_selected.jpg`). Look-pass alone has no role colour, no doors and no lamps, so for staged choices merged is better than B: the green/red answer to the owner's brief survives. B's shaft, glow and slit are the most striking effect, so they stay for single hotspots (`cmp_single_hotspot_bassment.jpg`, panels C) and are left off staged options. |
| Edge beacons | look-pass drawing, role-coloured | Main's beacon is a faint ring; look-pass's has a leak of light along the border, a ring with ripple and a white core (`cmp_wh_wizard.jpg`). Merged keeps that, in green or red; selected it keeps the circling motes. |
| Face-look facing fix (`StoryPlayer`, once per song time) | look-pass, taken whole | Not a picture: `pose_at` is asked for the same song time several times a frame, so the face look's five-sample facing is memoised on `t` (dropped when the schedule changes); covered by `tests/test_story_player.gd`. It is inseparable from the `face` look, which is why it comes with it. |
| Door and signpost choice (main A14) | main, untouched | Main's drawn doors, lamps and sign post render as before in C (`cmp_bar_selected.jpg`, `cmp_gospel_selected.jpg`); the merge only changes the rings and camera around them. |

**Not changed on purpose / found.** Main's docs call the "other" ring red and dashed; the code only coloured it (no dashes), and the merge does not add them. The Ember Road's first scene shows a very large pale checker door in both A and C (main's default drawn door at the orchard gate, its "door in the middle of a room until `door_at` is set" limit): not a merge effect. Phone-size shots (844 x 390) were not retaken (the `RW_WINDOW` variable is not read by my capture script).

**Verification.** Full `bash tools/test.sh` on the merged tree: **82,123 checks, 0 failures, exit 0** (14 minutes; origin/main alone was 82,082; the difference is look-pass's added tests and the two new ones in `tests/test_hotspots_view.gd`); Python content tests OK. The window matrix prints `window at beat 49, with the turn: 60 windows, a hotspot in view 60, the default 60, all 33; without: 60, 39, 26, 8`. `check_hotspots.py` main / gospel / squadron / ember: 0 errors (5 / 15 / 1 / 19 warnings, as on main). `walk_run.sh` (all walks of the main run: 36 of 36 scenes; gospel 17 of 17, squadron 14 of 14, ember 15 of 15, each `run walk-through: OK`). Not run: `walk_trial.sh`, `walk_campaign.sh`, `frames.sh` timings. The run and Bassment shots in `docs/shots/run` (all `hotspots_*` and the seven `contact_hotspots_*`) and `docs/shots/trial` that look-pass had retaken on its old base were retaken on the merged tree; `docs/shots/look_pass/` keeps the branch's own old-base pairs (their `.import` sidecars were dropped: `docs/` is `.gdignore`d). The Bassment textures were not regenerated: running `tex_bassment.py` here rewrites 84 PNGs byte-differently (machine-varying encoding, the known `check_assets.py --determinism` behaviour), so the committed bytes stay. Not verified: anything on a phone, phone-size shots, motion (the `face` turn and the beat ripple are only seen in stills), how it sounds (nothing audio changed).

## A16. The combined result: blackjack + look pass + choice clarity on one branch (5 November 2026, branch `integrate/all`)

`integrate/all` = `origin/main` (f79e1576) + the blackjack minigame (`feature/blackjack-minigame` and the room-table work of `wip/blackjack-polish-b`, merged as `integrate/blackjack`) + `integrate/look-pass` (A15). Nothing was pushed. No music, stem, pack or assignment file differs from main; the table is silent (no audio reference in `src/minigames`, `run_minigame_host.gd` or `run_card_table.gd`). The two blackjack branches are not a superset of one another: both forked at b0faaf08, one carries the exit doors, the house-look close-up and the guide, the other the table in the room (animated people, invitation, claim look); both are in. How the table works and how it sits on the three engines: `docs/BLACKJACK_INTEGRATION.md` 9.2 (every shared-file edit) and 9.12.

**Conflicts, and which side won.**

| File | Resolution |
| --- | --- |
| `src/run/hotspot_contract.gd`, `run_data.gd`, `run_hotspots.gd`, `run_engine.gd`, `run_progress.gd`, `run_hud.gd`, `tools/run/check_hotspots.py`, `tests/test_hotspots_engine.gd`, `content/run/run.json` | both kept: main's acting, pieces, laps, paths and DevText stay; the `activity` outcome, `window` "any", `pass_credit`, `on_select`, the lifecycle `hold`, the wallet, `RunHud.silent` and `max_hotspots` ride on top. `run.json` is regenerated by `tools/run/make_scenes.py` (two compact main lines restored by hand). |
| `src/run/run_play.gd` | both kept (blackjack's `# minigames` sites, `_claim_*`, main's playtest and path-leave code, look-pass's `face_fn`, `_window_face`, `_look_by`); `hotspot_items` carries `finished`, `t_commit`, `success`, and the committed state shows for `(FLASH_S + SETTLE_S) * 1.05`. |
| `src/run/hotspot_view.gd` | **look-pass's drawing, blackjack's claim look ported onto it** (`_light_claim`, `_marks_claim`, `_claim_*`; see 9.12). |
| `tests/test_hotspots_view.gd`, `tests/test_blackjack_integration.gd` | both test sets kept. |

**Three things the merge itself had to fix** (none of them is a conflict marker):
1. The choice layer staged the table as an option (`RunHotspots.staged` took every available hotspot): its ring was red ("another way") and touching it turned the day room's exits red. `staged()` now skips `window: "any"`; `tests/test_choice_clarity.gd` skips such a hotspot in its "touch each option" loop, and `test_hotspots_any_window.gd` has a test that the table is no option. (The first blackjack-only integration, `integrate/blackjack` 4a25c97b, has this red-ring bug.)
2. Look-pass's held `face` look (the head on the window's exits from the block-2 decision) kept the head on the exits after a touch of the table, so the camera did not walk to the table. A touch now releases the held look over two beats (`StoryPlayer.release_faces`, tested), and `_back_to_rail` re-frames the window if the last block's window is still open (the table was waved off, or the player got up).
3. The claim ring uses `look.ring_m` as before (the table's own size, not its touch radius).

**What the camera does in the ward.** Beats 49 to 51 (the window camera): the exits, the table and the people are all in the picture (`docs/shots/integrate_all/camera_beats_49_to_60_merged.jpg`, top row; the table's warm ring beside the exits' rings). A touch at beat 52: the head lets go, the camera walks to the table with the tip down; the swing past the table to the left around beats 55 to 56.5 is the same as on `integrate/blackjack` (`..._blackjack_only.jpg`, second row), not a regression; at beat 60 the table fills the picture with the claim ring and the countdown lamps. The window camera does not frame the table (`_window_face` lists only final-window hotspots).

**Pictures** (`docs/shots/integrate_all/`, taken with `tools/shoot.gd` on the virtual clock at 1280 x 720, the repo's capture script's environment): `30_invitation` (the free table: warm pool and ring, three players beckoning), `01_claim_at_the_table`, `17_32_18_19_33_touch_wait_refusal` (burst and arms up, the closing ring and lamps, the dark broken ring and the dealer's head shake), `07_seated`, `08_after_exit_tap`, `ward_window_and_warehouse_window` (a non-ward scene with the look-pass light and green role ring), the two camera sheets. The committed blackjack shots 01 to 33 in `docs/shots/blackjack/` are the branches' own and were not regenerated.

**Verification.** Full `bash tools/test.sh` on the final tree: **124,995 checks, 0 failures, exit 0, no SCRIPT ERROR in the log** (main alone was 82,082, blackjack-only 124,928; the Python content tests OK; about 20 minutes). `check_hotspots.py`: main, gospel, squadron, ember 0 errors (5, 15, 1, 19 warnings, as on main). `walk_run.sh`: main 36 of 36, gospel 17 of 17, squadron 14 of 14, ember 15 of 15, all `run walk-through: OK`. `export_smoke.gd` and `check_assets.py` OK on the blackjack-only tree (nothing in them changed since). A test that dies with a SCRIPT ERROR is not counted as a failure by the runner: grep the test log for `SCRIPT ERROR` as well as the totals.

**Not verified.** Phones and real frame times with the two-pass light plus the table (the table's per-frame cost was measured only before the look pass, section 9.11); the table's shots in `docs/shots/blackjack/` were not retaken on the combined drawing; a minigame inside a multi-lap path scene; the refusal and the touched-wait were looked at in one frame each, not in motion.


---

# Part B: the defense campaign and loadout (state of 3 November 2026, unchanged)

The text below is the earlier handover. Its commands, verified lists and backlog describe the defense-campaign code (missions, loadout, loop library), which is still in the repository but no longer on the home screen.

## What the game is now

A landscape phone rhythm defense game. Four illuminated pads play along with a 174 BPM drum and bass track; every
sequence of two bars you pass builds one defense or sends one unit; your Red Alert base in the middle of the screen
must keep its required buildings alive until the song ends. The player has one **loadout** (drum pattern, fill, kick
sound, snare sound, bass line, bass sound, backing track) that plays in every one of the ten missions and decides
what a passed sequence builds: kick sounds make infantry, snare sounds defenses, bass sounds vehicles. A mission is a
battlefield, a set of waves and a form (which 8-bar phases are drums and which bass); it authors no music. Home:
Continue, Campaign, Practice, Loadout, Settings, and a small Developer area (legacy duel free play, rhythm playtest,
content status, unlock-all status). Normal progression is on.

## How the game plays now

- **Pads.** Four large pads at fixed positions: 1 and 2 under the left thumb, 3 and 4 under the right (keys D F J K).
  Each phase of a mission follows one family. Drum phases: the loadout's kick sound is pad 1 and its snare
  sound pad 4 (pads 2 and 3 are dim). Bass phases: the bass line's notes spread over all four pads by pitch, lowest
  on pad 1 (a line with one pitch sits on pad 2), taps only, at least 1440 ticks apart (`data/campaign/rules.json`
  `chart.bass`, `tools/content/chart.py`). A pad with
  nothing to play in the current phase is dim; each lit pad carries the friendly name of its sound and a shape (kick
  disc, snare diamond, bass bars) as well as its colour. At most two touches count at once.
- **Cues (falling notes).** Every cue is a translucent pad-sized shape that falls straight down the screen, over the
  battlefield, and sits exactly on its pad at the hit time; a hold is a tall bar whose bottom square lands at press
  time and passes through until the tail. The note speed setting (0.6 to 2.0 s, default 1.2 s; `RW_LEAD_IN`) is how
  long a note takes from the top of the screen to its pad. A hit note vanishes, a missed one keeps falling for a
  quarter second tinted red; the pad still pulses on the beat, fills while you hold and flashes at the tail. One bar
  before a mode change a banner names the incoming family (BASS NEXT); there is no roadmap. Everything is drawn from
  the one song clock (`src/ui/note_lane.gd`; the closing rings of the earlier builds are gone).
- **Recognition (generous).** Perfect within 45 ms, great 90 ms, accepted 140 ms either side. One press takes the
  nearest cue of its pad; a second finger on a held pad does nothing; a press with nothing in reach is a stray.
- **Holds (forgiving).** Released within 0.15 s of the tail (or still held there) = complete; earlier = the held
  fraction counts, nothing fails. Pause ends a hold where it stands.
- **Sequences.** Missions cut each phase into sequences of two bars (a hold may run across a sequence boundary but
  never across a mode change; the sequence resolves when the hold does). A sequence passes at credit / cues >= 0.6 (taps 1 or 0, holds their coverage). A pass
  earns its **one** reward, a fail earns nothing and costs nothing already built. It resolves when its last cue is
  final, so it never rewards early and resolves the same at any frame rate.
- **Precision only sets speed.** Mean onset error of the accepted cues + 25 ms per stray per cue: sharp (<= 35 ms)
  builds in 0.5 s, steady (<= 70 ms) 1.5 s, loose 3 s. Mashing passes at best as loose. The centre of the pad strip
  shows the current sequence's progress against its threshold and what it will earn; the line under it says what was
  earned and how fast; the battlefield shows the socket being prepared with a countdown ring.
- **Rewards.** The loadout decides them, not the mission. Drum sequence k (counted over the whole mission) calls on
  the kick sound's instrument when k is even and on the snare sound's when odd, a bass sequence on the bass sound's
  (`data/campaign/instruments.json`; shares expand in order, so 2:1 is A A B and the cycle repeats). With the default
  loadout the first drum sequence sends a rifle squad and the second builds a pillbox. A reward the base cannot make
  (vehicles in the village, which has a barracks and no war factory) becomes a repair crew. Buildings (pillbox, gun turret, flame tower) go to
  prepared sockets (`data/battlefields/defense_02.json` and `village_01.json`, five per approach flanking each route
  outside the wall, `sockets_per_point` open per mission), approach with the fewest defenses first (ties: the approach
  most enemies are walking towards, else the next wave's). Units (e1 to e4, jeep, APC with its gun only, light and
  medium tank, artillery, flak truck; squads `rifle_squad` and `grenadier_squad` are three at once) come out of the
  barracks or war factory and hold the point with the fewest defenders (at most `units_per_point`, 6 by default, 14 in
  mission 1); they may sortie up to 16 cells to hit an enemy shelling their point from beyond their 6-cell leash.
  Reward units leave the barracks on attack-move and fight whatever they meet on the way; a defender beyond its
  leash keeps firing at a target in range but never chases it, and walks home fighting (`_leash_holds` in
  `battle_sim.gd`, `_defender` in `defense_ai.gd`). At capacity a reward becomes a repair crew for the most damaged
  approach or, with nothing damaged, +50% health once for the oldest defense; the status line above the pads says which.
- **Loadout screen and briefing.** Home > Loadout: one row per slot of cards (unlocked first, a locked card says what
  unlocks it), a strip of unit icons on every sound card, Listen on every card; choosing a card re-resolves the whole
  loadout (a slot that no longer fits falls back) and saves it. The mission briefing (`mission_setup.gd`) shows the base
  (a warning where there is no war factory), approaches, villagers, wave count and length, the loadout with what its
  three instruments build (vehicles struck out without a factory), "Change loadout", and for practice the part to play.
  The result screen names what a clear added to the loadout. No per-mission choices exist any more.
- **Sections (tap to deploy).** A tap on the battlefield (or keys 1 2 3) makes the nearest approach by x the active
  section: every reward goes there while it has room (else the normal choice) and a move flash plays. The Red Alert
  rally flag always stands at the current rally point (`Match.rally_point()`: the tapped section, else the point
  rewards would go to), drawn at full sprite size whatever the zoom. Nothing else is drawn on the map: no circles,
  numbers, brackets, countdown rings or wave arrows. The mission screen has no text overlay: the flag marks the rally
  point, EVA announces waves, buildings carry their own health bars, and the result screen reports sequences, units,
  villagers and objective health.
- **Zoom.** A battlefield's `view.zoom` (village_01: 0.75; absent = 1.0) scales the cell size (18 px instead of 24)
  and every sprite; missions 2 to 10 keep 24 px. The village is 96 x 48 cells (`data/maps/field_96x48.json`), the
  view 72 x 27 cells, the rally points 7 cells outside the side walls and 6 above the top wall, the entries 5 cells
  beyond the window; `python tools/campaign/build_battlefield.py village_01` regenerates only the village files.
- **Bass chart.** The charting rule is global (`rules.json` `chart.bass`: `pads: pitch`, `min_gap_ticks: 1440`,
  `holds: false`; `tools/content/chart.py`): the bass line's pitches map to pads 1 to 4 from low to high and at most
  one note per 1.5 beats is cued, every cue a tap; the recording still plays every note. The cues are baked into the
  library index per clip (`songs/library/index.json`), so a new bass line is charted by the build.
- **Misses.** A missed cue (or a hold released with nothing held) silences that instrument's stems until the next hit
  on it (`Match._judge_to_stems`); the backing track never mutes; at a phase change every family the new phase does
  not cue comes back; a muted family's pad label draws at half alpha.
- **Civilians (mission 1).** The village map has ten houses (OpenRA `v01`..`v08`) and ten civilians (technicians
  drawn as `c1`, villagers `c2`) that wander between the houses, flee from enemies within 6 cells and die when shot;
  they never fight or repair, player units ignore them, and the result screen reports "Villagers lost x of y".
- **Sound.** `src/audio/battle_sfx.gd` plays the Red Alert effects in `assets/sfx/` (33 Ogg files extracted from the
  owner's install by `tools/extract_openra_sounds.py`) from the simulation events through `data/sfx_map.json`:
  weapon reports (M1 carbine, M60, Vulcan, grenade), kaboom and crumble on destruction, dedman screams, civilian
  cries, placbldg/build5 on pillboxes, EVA "unit ready", "enemy units approaching" (8 s before a wave), "base under
  attack", "unit lost", "mission accomplished/failed", an allied "acknowledged" on a section tap; 12 players, 8
  voices, cooldowns, EVA lines queued one deep. Mix (3 Nov, after the owner's first play): shots at −18 dB with a
  0.25 s cooldown per weapon and at most 3 weapon voices at once (`group_voices`), deaths −14/−12, explosions −10,
  build sounds −8, EVA −6, outcome −3, a limiter at −1 dB on the SFX bus, Effects slider default 50% (a saved
  settings file without `mix_version` 2 is reset to it once). Music plays on its own "Music" bus. Nobody has
  listened to the mix: the owner judges it.
- **Waves** are authored by bar per mission (`data/campaign/waves/level_NN.json`), never depend on accuracy, walk on
  from off screen at the left, top and right, attack-move via their approach's defense point to their objective and
  fight units **and defensive structures** on the way (not other buildings). A wave (or a group) may carry a
  `target` class: `defenses` (fight at the choke point and hold there), `civilians` (then the nearest house or
  villager), `core` (the objective, the default); a class falls through to the next inward one when nothing of it is
  left. A mission's level rules may add `start_units` (mission 1: five riflemen at each point) and `units_per_point`.
  Required objectives: the command core (missions 2 to 10), the barracks (mission 1), plus the power plant (6, 10) or
  radar dome (8, 10). Survive to the end of the song to win; lose a required objective and the run ends.
- **Progression.** Clearing mission n unlocks mission n+1 and the library items (clips and sounds) listed in its
  `new_options` (`data/campaign/campaign.json`); the default loadout is always available; no accuracy threshold blocks
  the ladder. The save (`user://campaign.json`) is version 3 `{cleared, loadout, last_played}`; versions 1 and 2 migrate
  on load (clears and bests kept, per-mission selections dropped, the loadout becomes the defaults; the old file is
  kept as `.v1` or `.v2`); settings v1 keep
  calibration and the last pack, and the cue lead-in starts at its default (the old note-approach time measured
  something else).

## The ten missions (owner's view; the menus show names and locks only)

The missions are bases and waves now; the music is the player's loadout. Form = the 8-bar phases (D drums, B bass).
The last column is what clearing the mission adds to the loadout library (`new_options`; every mission also adds its
own backing track, named "<Mission> accompaniment").

| # | Mission | Length | Form | New for the player | Enemies (first appearances) | Objectives | Unlocks on clear |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | First Watch | 128 bars, 177 s | DDBDBDDBDBDBDDBD | the village map (three choke points with five riflemen each, ten houses and ten civilians, the barracks in the middle), tap-to-deploy sections; four acts: waves at the choke points, then the village, then raiders with jeeps, then the barracks | e1, e2, jeep | barracks | the starter kit and every first-set sound, groove and bass line (Half-Time, Double Step, Rolling, Sub Line, Reese Line, the nine bass sounds, three hats) |
| 2 | Second Pulse | 40 bars, 55 s | DDDDD | | e2 | core | Push, Straight, Crack Snare |
| 3 | Hold the Line | 48 bars, 66 s | DBDBDB | bass phases | e3, 1tnk | core | Patrol Sub, Reese, Long Line, Answer Line (ending) |
| 4 | Backbeat | 48 bars, 66 s | DDDDDD | | e4, apc | core | Two-Step, Siege Kick, Field Clap, Snare Run |
| 5 | Counterpoint | 56 bars, 77 s | DBDBDBD | | | core | Steps, Growl, Answer Line |
| 6 | Fortress | 56 bars, 77 s | DDDDDDD | | 2tnk, arty | core + power plant | Roller, Heavy Kick |
| 7 | Crossroads | 64 bars, 88 s | DBDBDBDB | | ftrk, v2rl | core | Command Saw, Octaves |
| 8 | Crossfire | 64 bars, 88 s | DDDDDDDD | | 3tnk | core + radar dome | Break, Rimshot |
| 9 | Iron Rhythm | 64 bars, 88 s | DDBDDBDD | | 4tnk | core | Kick Drop |
| 10 | Last Light | 80 bars, 110 s | DDBDBDBDBD | | all 13 ground actors | core + plant + dome | Hollow Sub |

Each mission's design notes are in its `note` fields (`content/missions/level_NN.json`, `data/campaign/waves/level_NN.json`).
Missions 5 to 10 carry start units, prebuilt defenses and bigger objective hp from the loadout retune (3 November, night).
The coverage matrix of every ground actor and building is in `docs/BALANCE.md`, with the per-seed results.

## Content: loop library, missions, the one build command

- `content/library/<clip>/`: mission-independent clips at 174 BPM 4/4 with stable ids (31 clips: grooves and fills
  with kick and snare parts, bass lines, backing tracks), one MIDI per part, a `clip.json`. **Eight clips are the
  owner's Ableton exports** (`ToAddTry1/`, manifest `content/imports/first_watch.json`): three eight-bar grooves
  (Half-Time, Double Step, Rolling), two bass lines (Sub Line with five recordings, Reese Line with four) and three
  audio-only backings (Driving, Busy, Offbeat Hats). Each declares the sounds it was recorded with (`sounds`), so it
  plays only its own recordings. The rest are cut from the First_Three MIDI (hashes checked on every build) or
  generated; they play placeholders until the owner renders them.
- `content/sounds.json`: 30 sounds (14 synthesised, 16 recorded). `data/campaign/instruments.json` says what each
  sound produces in battle (reward ids with shares) and its blurb; the build refuses a sound without an entry.
- `content/missions/level_NN.json`: one mission, nothing else: `level_id`, `number`, `title`, `pack`, `bars`, `seed`,
  `form`, `battle` (battlefield, waves, rules), `intros`, `note`. `content/missions_legacy/` keeps the old authoring
  (choices, phases, stems); only `tools/content/export_midi.py` still reads it.
- **The build, one command**: `python tools/content/build.py [level_NN ...]` (`--check` validates only). It builds
  the library first: `songs/library/index.json` (sounds with their rewards, clips with cues per part and the loop file
  per part and sound, defaults) and `songs/library/loops/` (**117 loops, 5.9 MB**, one Ogg per clip part and sound,
  exactly 8 bars, backings 16; unchanged loops are not re-encoded), then every mission's `songs/mNN_*/level.json`
  (schema 4: phases, waves, rules, base, intros; no audio), `content/REPORT.md`, `docs/CONTENT_TO_RENDER.md` and
  `data/campaign/library_names.json`. **About 23 s from scratch**, under a second when nothing changed; the index and
  packs are byte-identical when nothing changed. After editing a waves file rebuild that mission (`level_NN`, about a
  second) and run `--import` once. Schema 3 packs and the 9-minute stem assembly are gone.
- **Charts and checks**: kick cues are pad 1, snare cues pad 4, bass cues by pitch (above). The build checks every clip
  against the pad gap rules (same pad 480 ticks, same thumb 480 between pads) and every groove together with every
  fill (the groove's bars 1 to 7 and the fill's bar 8); an error names the clip or the pair. It does not test the loop
  seams (a tail that rings past bar 8 is folded onto bar 1 by construction; nobody has listened).
- **Owner renders** still go to `content/library/<clip>/<part>__<sound>.wav` (48 kHz stereo 16-bit, from the clip's
  bar 1, at most one bar of tail), then rebuild; a MIDI edited in Ableton regenerates the clip's cues and the build
  refuses WAVs rendered from the old MIDI. The exact list is `docs/CONTENT_TO_RENDER.md` (31 clips, 117 renders, 18
  of them the owner's recordings already in place), rewritten by `python tools/content/render_list.py`.
- **The importer path** for an Ableton batch is unchanged: `python tools/content/import_ableton.py <manifest>
  [--check]` files 44.1 to 48 kHz exports into the library (SoX resampler, no time-stretch; MIDI cut to the clip's bars
  at 960 PPQ with 174 BPM written in; WAVs cut to the bars plus a sounding tail of at most one bar; gain rules, a global
  trim and a 10 ms end fade; originals untouched). `content/README.md` has the manifest format and the steps for new
  phrases; a new clip also needs `produces` entries only if it brings a new sound.
- **MIDI for the owner's renders (missions 2 to 10)**: `python tools/content/export_midi.py` reads `content/missions_legacy/`
  and writes `midi_export/level_NN_<slug>/` (3 November 2026): 8-bar loops `Kick_A/B/C`, `Snare_A/B/C`, `Bass_A/B/C`,
  `Other_Pad`, `Other_Hats` and a reference `Arrangement_A.mid` per mission, a README per folder and a manifest template
  `content/imports/level_NN.json`. Under the loadout model the exported loops are simply more library clips once the owner
  renders and imports them; `tools/content/test_export.py` proves determinism, the bounds and a synth round trip.
- **Placeholder WAVs** for reference are in `content/library/<clip>/placeholder/` (git-ignored, regenerated
  identically by the build on a fresh checkout); the game plays the Ogg loops in `songs/library/loops/`.

## Verified and not verified

Verified (31 October 2026, this PC, headless unless stated):
- `bash tools/test.sh`: 1,793 GDScript checks and 9 content build tests, 0 failures. One expected
  `Parse JSON failed` line is the corrupt-save test. Covered: cue and hold recognition, generous acceptance versus
  precision speed, sequence pass/fail and one reward each, mash and duplicate presses, pause and retry determinism,
  phase continuity of the stems, socket placement and capacity, all ten missions loading with every option and
  completing (perfect wins every sequence, no input loses), progression and unlocks, save v1 migration, the legacy duel.
- The 18 First_Three MIDI hashes match `campaign/Musical_Source_Integrity.json` (checked by the build and a test).
- Seeded balance (`docs/BALANCE.md`): perfect 60 of 60 and beginner 60 of 60 wins over seeds 1 to 6, sloppy 27 of 30,
  no input 0 of 30.
- Sample-exact clip placement in the assembled stems (content test, within one sample).
- Screens looked at by the agent in real windows at 1280 x 720 and 1600 x 720: home, missions, mission setup
  (mission 1, 7 with locks, 10 with every choice), settings, play with pads and holds, pause, result. Not by a person.
- Desktop real-window run of mission 10 with perfect autoplay: see `docs/BALANCE.md` (frame time).
- Exports: see "Exports" below.

Verified (3 November 2026, evening: falling notes, no top bar, rewards every 2 bars with doubled waves, the MIDI
export; this PC; see `docs/BALANCE.md` "Rewards every 2 bars, every wave doubled"):
- `bash tools/test.sh` green: 10,730 GDScript checks and 48 content tests (12 of them `tools/content/test_export.py`).
  New: `test_note_lane.gd` (the shape equals the pad at the hit time, leaves the screen top at the note speed, holds
  grow upward, visibility window and states, the duel path); the mission tests now expect 64 sequences, 9 or 10
  built, 36 units, repairs, every wave destroyed under perfect play; the content tests 64 sequences, at least 260
  enemies, 6 jeeps; the export tests determinism, bar counts, A equals the library, B/C within bounds, manifests,
  and a synth round trip through `import_ableton.py --check` on mission 4.
- Seeded balance recorded (seeds 1 to 3, no retune): missions 1 to 5, 7, 9 win under perfect and beginner play;
  mission 6 drops one beginner seed; missions 8 and 10 lose under perfect play with the doubled waves (known,
  retune after the loadout round). Mission 1: 64 of 64 sequences, all 278 enemies destroyed, villagers 0 of 10 lost.
- Real 1280 x 720 window with perfect autoplay to VICTORY (mission 1) and into act 2 (mission 3): the notes fall
  over the village and sit on their pads at the hit time, no band at the top, the flag on the map, the centre meter
  and "Pillbox ready" line still there, the result screen with 64 of 64. Not by a person: nobody has felt the note
  speed (default 1.2 s), the reward pace or the doubled waves by hand; the MIDI has not been opened in Ableton.

Verified (3 November 2026, later: the first-play tweaks, this PC; see `docs/BALANCE.md` "after the owner's first play"):
- `bash tools/test.sh` green: 10,472 GDScript checks and 36 content tests. New or rewritten: `test_village_sim.gd`
  (a reward unit fights an enemy on its way to its point and still arrives; a defender beyond its leash walks home
  without chasing), `test_miss_mute.gd` (miss mutes, hit restores, bass miss leaves kick alone, backing never mutes,
  phase change restores, restart unmuted), `test_battle_sfx.gd` (shots −18 dB, every rule at most −3 dB, weapon
  group cap 3, limiter on the SFX bus), the mission 1 tests (252 default cues, 72 bass taps on pads 1 to 4 at
  least 1440 ticks apart, no holds, perfect play still destroys all 25 waves, villagers lost at most 4),
  `test_mission_layout.gd` and `test_rewards.gd` through `BattleView.cell_px`, the content tests (`BassChartTests`,
  the village battlefield values).
- Seeded balance, seeds 1 to 3: mission 1 perfect, beginner and sloppy 3/3 each with all 139 enemies destroyed, no
  input loses at about 1:41; missions 2 to 10 re-run with the new defender behaviour: three late losses appeared,
  two fixed by raising objective hp (mission 5 core 130,000, mission 8 radar dome 70,000); mission 10's core went
  to 185,000 and its beginner seed 3 still falls at 108.0 s of 110.3 (known, see `docs/BALANCE.md`).
- Real 1280 x 720 window with perfect autoplay to VICTORY: screenshots of the zoomed village (wall ring, all three
  points and the rally flag on screen, the flag moving with the suggestion; the "RALLY: LEFT (auto)" top-bar text of that build is gone), a bass phase with "Deep
  Sub" on all four pads, act 2 fighting at the left point, the result screen. Not by a person; nobody has heard the
  mix, the miss muting or the bass chart; nobody has tapped by hand.
- Latent build bug fixed in passing: since 2 November `python tools/content/build.py` failed on missions 8 and 10
  ("choice kick_sound pairs with several clip choices") because their kick and snare sound choices are shared by the
  groove and the fill; `_choice_entries` now follows only a restricted parent. Both packs rebuild again.

Verified (3 November 2026, the village level, this PC; see `docs/BALANCE.md` "The village level"):
- `bash tools/test.sh` green: new suites `test_village_sim.gd` (civilians, start units, target classes, squads, the
  active section), `test_civilian_art.gd`, `test_section_input.gd`, `test_battle_sfx.gd`, the rewritten mission 1
  tests (128 bars, 32 sequences, every wave destroyed by perfect play for every groove and bass line, villagers lost
  at most 4, no input loses), `tools/test_extract_openra_sounds.py` and the content tests for the village map.
- Seeded balance, seeds 1 to 3: perfect 3/3 with all 139 enemies destroyed, beginner 3/3, sloppy 2/3, no input 0/3
  (the barracks falls at about 97 s). Missions 2 to 10 produce byte-identical harness reports to before.
- Real 1280 x 720 window with perfect autoplay to VICTORY; screenshots of the village, the flag after a tap on each
  section, the move flash, the acts and the result screen with villagers. Not by a person; no sound heard by anyone.

Verified (2 November 2026, the Mission 1 rebuild, this PC):
- `bash tools/test.sh`: 2,854 GDScript checks and 20 content build tests, 0 failures. New: `tests/test_mission_one_content.gd`
  (all 81 combinations of groove x bass line x bass sound x backing load with their own stems and cues; a Sub recording
  asked for with the Reese line is swapped for the first Reese recording with a warning; defaults, 12 sequences, 6
  phases, 102 notes with every bass note a hold on pad 2, pad names from the bound sounds, both intro lines; perfect
  play wins with 12 of 12 sequences, 7 pillboxes, 5 jeeps and all 56 enemies destroyed for every groove and line; no
  input loses) and `tools/content/test_import.py` (11 tests on synthetic 44.1 kHz exports: format and length, attack
  timing against the MIDI, MIDI cut and tempo, gain, trim and fade, declarations, idempotence, pairing in the pack,
  refusals, the mode-change warning, `--check` writes nothing).
- The imported audio, by analysis (not by ear): every render is exactly 8 bars at 174 BPM (529,655 frames at 48 kHz),
  drum onsets match the MIDI within about 5 ms, the exact worst-case mix over all 81 combinations peaks at -3.03 dBFS
  and the default mix at -4.26 dBFS, the assembled stems have no clipping and no step at a loop or phase boundary
  larger than the file's own 99.9th-percentile sample step, the tail after the song end is below -43 dBFS.
- Seeded balance of the new Mission 1 (`docs/BALANCE.md`): perfect 3 of 3 wins with every wave destroyed, beginner 3
  of 3, sloppy 3 of 3, no input 0 of 3.
- Real 1280 x 720 window, `RW_MISSION=1 RW_SCENE=play RW_AUTOPLAY=perfect`: plays to VICTORY (12 of 12, holds 30 of
  30, 7 defenses, 5 units), 4 streams, 3,964 frames, average 16.7 ms, 2 frames over 33 ms (loading), 53 MB static.
  Screens looked at by the agent: mission setup with the four rows (Drum groove, Bass line, Bass sound filtered by
  the line, Backing track) before and after switching to the Reese line, the play screen in a drum phase and in a
  bass phase, the result screen. Not by a person.

Verified (3 November 2026, night: loadouts; this PC; see `docs/BALANCE.md` "Loadouts"):
- `bash tools/test.sh` green: 11,663 GDScript checks and 62 content tests. New or
  rewritten: `test_library_index.gd`, `test_loadout.gd`, `test_loadout_screen.gd`, `test_transport.gd` (loops, longest
  first, unwrapped position), `test_campaign.gd` (save v3 and the v2 migration), `test_mission_one_content.gd`,
  `test_all_missions.gd` (782 checks: every mission loads and perfect play wins it).
- Seeded balance, default loadout, seeds 1 to 3: perfect 30 of 30, beginner 29 of 30 (mission 9 seed 3 loses at 87.2 s of
  88.3), no input 0 of 30, sloppy 14 of 30; seeds 4 to 6: perfect 30 of 30, beginner 28 of 30 (mission 8 seeds 4 and 5).
  Mission 1 perfect destroys 266 to 271 of 278 enemies (96 to 97%) and loses 0 of 10 villagers. Heavy loadout, untuned:
  perfect 30 of 30, beginner 30 of 30, no input 0 of 30; mission 1 destroys 213 to 237 of 278.
- The finding behind the loop engine: Godot's player position wraps at the loop length over looping
  `AudioStreamSynchronized` substreams (test output `FINDING: ... WRAPS`), so the transport unwraps it.
- **Not verified, loadouts:** nobody has heard the loops switching at phase boundaries, the fill bar or the loop seams
  (the build checks lengths and cues, not the sound); nobody has used the Loadout screen or the briefing by hand
  (the agent ran the scene tests only); nothing has run on a phone; the 117 loops include 99 placeholders.

**Not verified:** any phone run (touch feel, the two-thumb layout, frame time and memory with 16 Ogg streams on a
phone CPU, load time of mission 10), any listening check by ear (the build and the importer check sample positions,
lengths and headroom only; nobody has listened to the assembled Mission 1, its previews or the Red Alert effects in
the game), any human playtest of the cues, sequences, difficulty or the tap-to-deploy feel (the beginner and sloppy
policies are models; the harness taps the suggested section every frame), real owner renders for missions 2 to 10
(none exist yet; Mission 1's are real), the screens on a real phone's safe areas and DPI, the `make` animation on a
rewarded pillbox (only plays if the actor has that sequence).

## How to run the phone check (the owner's)

1. Install: `adb install -r build\android\RhythmWarfare-debug.apk` (or rebuild it first, `docs/EXPORT.md`).
2. Open the app, Settings > Calibrate once, then play mission 1 (Continue). For the heaviest case set
   `"unlock_all": true` in `data/campaign/campaign.json` and re-export, or play through, and run mission 10.
3. `adb logcat -s godot` prints a `PERF {...}` line when a run ends (p95 frame time, frames over 33 ms, peak units).
   Report that line, whether any press felt missed, whether the pads sit well under the thumbs, and the cue lead-in
   that felt right.
4. Settings has pad size, cue lead-in, high contrast, reduced effects, vibration and music volume.

## Owner decisions that are settled (do not re-ask)

From `docs/BRIEF_PADS_SEQUENCES_TEN_MISSIONS.md` Part A (31 Oct 2026): pads only (lane view dropped), one pad per bass
voice (the level 3 four-button bass chart and the thumb-gap rules are archived), a loop library at 174 BPM with
stable ids, offline assembly by one build command (no runtime clip engine, no in-game import screen), sequence rewards
replace per-note recipes, loadout caps and round robin, the legacy duel stays, holds are forgiving, early rewards are
static defenses first, wave units fight defenses, no slow practice, generated music for all ten missions, normal
progression on by default with `unlock_all` as a developer switch, the save migrates. Earlier: standalone Godot 4.5.1;
DuelMasterBattle is an asset source only; OpenRA pixel art and behaviour; work on `main`.

From the loadout redesign (3 Nov 2026, night; the owner's four answers): all music comes from the player's loadout (a
mission authors none); the arrangement is the pattern (the clip's own cues, tiled over the phases, are what is
played); instruments decide the units by family (kick sounds infantry, snare sounds defenses, bass sounds vehicles);
recordings are tied to their patterns (a clip plays only the sounds it was recorded with). Earlier loadout choices of
the 31 October brief (per-mission pools and counts) are retired with them.

## Decisions made in this build (routine design details)

1. Pad mapping and windows as above (`data/campaign/rules.json` holds every number).
2. Sequence threshold 0.6; precision grades 35 / 70 ms; 25 ms per stray per cue.
3. Placeholder WAVs are not committed (133 MB); the build regenerates them deterministically.
4. Missions 1 to 3 keep their First_Three bar counts; missions 4 to 10 grow from 48 to 80 bars.
5. `fix` (service depot) is not used: the simulation has no unit-repair behaviour. `agun`/`sam` are AA-only and unused
   (no air threat). The APC is named "APC (gun only)" because it carries no troops.
6. Defenses measure range from their footprint edge in missions (flame towers could not reach riflemen otherwise);
   defenders sortie against outranging artillery and V2s. Both are mission-only, so the duel's results are unchanged.
7. Practice is the same mission with the battlefield hidden and nothing saved; the setup screen can practise one phase.
8. Mission 10's pools were trimmed to keep it at 16 streams and about 14 MB of Ogg.
9. Village level (3 Nov 2026, owner's calls): infantry only for the player, a few enemy jeeps in act 3; civilians are
   atmosphere (wander, flee, die, counted; never repair; never required); a tap sets the active section until the next
   tap (rewards before any tap are placed as before); rewards are pillboxes and rifle squads, grenadier squads from act
   3; 128 bars; the barracks is the one required objective with 60,000 hp; civilians are side-0 entities with a
   `civilian` flag (never a third side: every sim array is indexed by side); the sim uses a separate `civ_rng` for
   wandering so combat outcomes of other missions are unchanged; the autoplay harness taps sections only on levels
   with civilians (`RW_SECTION=auto|none|fixed:<i>`), because tapping the next wave's point every frame makes mission
   5 lose.
10. First-play tweaks (3 Nov 2026, owner's calls): bass pads by pitch low to high, taps only, one cue per 1.5 beats
    (the owner asked for one per beat; at one per beat the Reese line kept all 23 of its notes, so the gap is 1440
    ticks); a miss silences the instrument until the next hit on it; zoom three quarters with the rally points
    further out; units fight on the move but a defender never chases beyond its leash.
11. No top bar in missions (3 Nov 2026): the owner found it noise; nothing is drawn over the map but the flag and the
    units' own bars. The wave warning line went with it (the EVA voice still warns).
12. Falling notes (3 Nov 2026, owner's call): the closing rings did not work for the owner; notes fall over the
    battlefield from the top of the screen so the map and pads keep their size (a lane band between them would have
    shrunk the map the owner had just zoomed out). The shape equals the pad at the hit time.
13. Rewards every 2 bars with every wave doubled (3 Nov 2026, owner's calls); the threshold stays 0.6, so a drum
    sequence needs 3 of 4 or 5 taps and a bass sequence 2 of 3. Capacity is the first balance lever (mission 1 keeps
    14 units per point; missions 6, 8 and 10 got 12), objective hp the second; wave counts and sequence length are
    not touched by balance.
14. MIDI export choices: the exported loops mirror what the missions play (the default groove tiled with the default
    fill in bar 8), alternatives are rule-based and seeded by the mission seed (at least one edit per two bars, at
    most a quarter of the notes), ghosts go an eighth before a backbeat because a sixteenth would break the pad gap,
    missions without a bass phase get a root-note `Bass_A` so the owner can add bass later.
15. Loop engine (3 Nov 2026, night): the game plays 8-bar Ogg loops (one per clip part and sound) as substreams of the
    one `AudioStreamSynchronized`, `loop = true`, longest first, gain switched per bar by the pack's gain program;
    no assembled per-mission stems. The finding: the player's playback position wraps at the loop length, so the
    transport counts wraps (`song_base + wraps x loop_seconds + raw`) and everything else keeps one unwrapped clock.
    A fill plays in bar 8 of every eight (its stems on, the groove's off).
16. Even/odd rule: a drum sequence k takes the kick instrument's next reward when k is even and the snare's when odd
    (counted over the whole mission), a bass sequence the bass instrument's; each cycle advances once per use. Chosen
    because it needs no mission data and keeps both drum sounds in play.
17. Defaults: the default loadout is mission 1's kit (Half-Time, no fill, Half-time kick, Backbeat snare, Sub line,
    Deep sub, Driving hats); the player's saved loadout starts there; `loadouts.json` also has `village` (the same) and
    `heavy` for the tools.
18. The village has no war factory, so bass sounds (vehicles) give repair crews there; the briefing says so and strikes
    the vehicles out of the unit strip. Missions 2 to 10 have a factory.
19. Acc backings cut to 16 bars: the generated backing clips were 32 to 48 bars, the loop library keeps their first 16
    (10 ms fade); a backing loops under the whole song.
20. The campaign ladder lists every pickable library item (clips and sounds, 57 ids): mission 1 lists 26 (the starter
    kit and its first set), missions 2 to 10 a few each plus their own backing track.
21. Loadout retune (3 Nov 2026, night): missions 5 to 10 got start units (five riflemen per point, rocket soldiers and
    medium tanks in 9 and 10), prebuilt pillboxes and turrets, bigger objective hp and `units_per_point` 12 (mission
    10: 20); start units count against `units_per_point`, so the default 6 turned reward squads into repairs. Wave
    counts, timing, the sequence length, the threshold and the instruments were not touched.

## How the code is organised

- `src/core/`: `library_index.gd` (reads `songs/library/index.json`: clips, sounds, cues, loops, compatibility),
  `loadout.gd` (the slots, `resolve`, reward cycles), `mission_loader.gd` (schema 4: loadout -> stems, cues, sequences,
  gain program; schema 2 and 3 packs are refused), `mission_rules.gd` (rules.json),
  `sequence_tracker.gd`, `match.gd` (mission flow: judge -> sequences -> rewards in the tick loop; and the duel flow),
  `campaign.gd` (ladder, unlocks, save v3 with the v1 and v2 migrations, the loadout), `session.gd` (settings v2, `start_mission`, env
  overrides), `level.gd`, `level_loader.gd` (schema 1 duel and dispatch; schema 2 is refused as retired), `song_clock.gd`.
- `src/input/pad_judge.gd` (missions), `judge.gd` (duel), `lane_input.gd` (touches and keys D F J K).
- `src/sim/battle_sim.gd` (deterministic 25 Hz OpenRA simulation; mission sockets, rewards with `count`, capacity,
  walls, prebuilt defenses, `start_units`, civilians and village buildings, wave target classes, the active section),
  `defense_ai.gd` (defenders hold and sortie, waves walk via their point then chase their class's goal, civilians
  wander and flee), `bot_ai.gd` (duel only).
- `src/ui/`: `pad_view.gd`, `battle_view.gd` (sprites only, three layers: neutral civilians, blue, red; the rally flag
  and move flash), `hud.gd` (the legacy duel's bar only; missions have no text overlay), `section_picker.gd`, `ui_style.gd`, `settings_panel.gd`, `sprite_bank.gd`.
- `src/audio/`: `stem_transport.gd` (the song: looping substreams, the unwrapped position, the gain program, on the "Music" bus), `battle_sfx.gd` (effects on the "SFX" bus from
  `data/sfx_map.json` and `assets/sfx/`).
- `tools/extract_openra.py` (sprites from the owner's OpenRA content, allow-list `NEEDED`, aliases `flagfly`),
  `tools/extract_openra_sounds.py` (AUD decoder and the sound list), `tools/campaign/build_battlefield.py`
  (`defense_01`, `defense_02`, `village_01`).
- `src/scenes/`: `main_menu`, `missions`, `mission_setup` (the briefing), `loadout` (`loadout.gd`/`.tscn`, the Loadout
  screen), `play`, `result`, `settings`, `calibration`, `developer`.
- `tools/content/`: `build.py`, `library.py`, `mission.py`, `chart.py` (the pitch-to-pad bass chart), `synth.py`,
  `common.py`, `render_list.py`, `export_midi.py` (reads `content/missions_legacy/`), `make_fixtures.py`,
  `test_content.py`. `tools/autoplay.gd` (harness), `tools/balance_missions.py`, `tools/shoot.gd`.
- Retired and removed: schema 2 and 3 packs and their assembled stems and previews (the schema 3 paths in `songs/mNN_*/audio`
  and `preview`), per-mission choices, schema 2 packs, the 30 October loadout screen (the current Loadout screen is new), `lane_view.gd`, the instrument catalogue, the campaign wave
  generators and `audio_preflight.py`. `docs/CAMPAIGN_PLAN.md` is kept with a superseded banner.

## Exports

Rebuilt on 31 October 2026 per `docs/EXPORT.md` (`build/` is git-ignored):
- `build/android/RhythmWarfare-debug.apk`: 95.8 MB (was 42.8 MB with three missions), debug-signed, arm64-v8a, all ten
  mission packs inside. Not installed on a phone by the agent.
- `build/windows/RhythmWarfare.exe`: re-exported 3 November 2026 with the village level, 232 MB (the 27 MB mission 1
  pack and the sounds); `[ DONE ] savepack`. Not smoke-tested that day: Windows Application Control blocked the fresh
  exe from the agent's shell, so the owner runs it. The 31 October smoke test was `RW_MISSION=10 RW_SCENE=play
  RW_AUTOPLAY=perfect RhythmWarfare.console.exe --headless` (mission 10 to the end with 16 streams, no errors).
- The Android APK was not rebuilt on 3 November (the owner declined on 2 November); it still holds the 48-bar mission 1.
- The APK grew because every offered combination of every mission is pre-assembled (67 MB of Ogg). If that is too
  large, trim the option pools of missions 7, 9 and 10 or lower the Ogg quality in `tools/content/common.py`.

## Known issues and backlog

1. Real stems for missions 2 to 10, the phone run and a human playtest (above). Retune waves after the owner has
   played; the numbers are a harness's, and outcomes from mission 5 on are seed-sensitive.
1a. Mission 1 on the owner's recordings: the 16 sound names and 8 clip names are provisional; the Sub Line's last note
   ends on the bar line where the next drum phase's first kick is cued (bars 25 and 41, same thumb: the build warns,
   the game credits a release up to 0.15 s early, mission 3 has the same shape); the bass sound row offers nine
   recordings, shown five or four at a time by bass line; the pads are two thumbs wide apart and the bass phases use
   pad 2 only, so a phone's feel is unknown; `content/REPORT.md` reports the loudest-options bound (-1.59 dBFS, a
   10 ms block envelope) while the exact worst case is -3.03 dBFS.
2. Wave units of one group can stack on one exact point while grinding a target (they separate when moving).
3. A wave jeep can loiter inside the base targeting the core without doing damage (seen once while tuning mission 7).
4. The autoplay report's `reached_s` equals the spawn time for left-entry waves (a report bug, not a game bug).
5. Headroom is checked for each mission's default selection only; louder combinations (for example Heavy Kick with
   Command Saw in missions 7 and 9) may clip slightly. Owner renders change this anyway.
6. (Gone: the library build takes 23 s and re-encodes only changed loops.)
7. Mission setup on very wide screens leaves the right half of the cards area empty (functional, not pretty).
8. Duel backlog items (idle fidgets, ruins, title art) still apply; the duel has no sound effects (the sound layer is
   wired in the mission play scene only).
9. Village level: a unit behind a house can draw over it (civilians and houses are one layer under both armies); the
   "defenses" waves that hold a choke point count as uncleared when the player never retakes it (sloppy runs); the
   pack is 27 MB of Ogg (18 stems x 129 bars); the sounds `reinfor1`, `bleep11`, `cashturn` are extracted but
   unused; no positional panning; at zoom 0.75 sprites are decimated with nearest filtering (linear would break the
   faction remap shader); the rally flag is small on a phone; the Reese line leaves pad 4 unused.
10. (Superseded by the loadout retune: mission 10 now holds under perfect and beginner play with core 400,000 and a bigger
    start army, `docs/BALANCE.md`.) Mission 10 beginner seed 3 lost at 108.0 s of 110.3 with the old reward lists.
11. (Done in the loadout retune, 3 Nov 2026, night: missions 6, 8 and 10 hold under perfect play with the default
    loadout; see items 14 and 15 for what is left.) With every wave doubled the evening run had lost them.
12. The falling notes are pad-sized and at alpha 0.4 read as solid blocks over the dark field; if the owner finds
    them heavy, `NoteLane.FILL_ALPHA` and the outline are the knobs. The hold bar of a two-bar hold is taller than
    the screen (by design: it keeps passing through the pad).
13. Loop seams: the build checks loop lengths and cues, not how a seam sounds; a ringing tail is folded onto bar 1 and
    nobody has listened to it, to the gain switches at phase boundaries or to the fill bar.
14. Heavy loadout (untuned, `docs/BALANCE.md` "Loadouts"): wins every mission under perfect and beginner play, but
    in mission 1 perfect play destroys only 213 to 237 of 278 enemies (77 to 85%) because its infantry is grenadiers and
    rocket soldiers; a retune for it would need start units or waves, not done.
15. Default loadout, known losses after four tuning rounds: mission 9 beginner seed 3 (87.2 s of 88.3, overwhelmed late),
    mission 8 beginner seeds 4 and 5 (the radar dome falls at 81 to 82 s); sloppy play loses most of missions 2, 4, 6, 8.
16. The bass sounds make vehicles, which the village (mission 1) cannot build: its bass sequences are repair crews.
17. The Windows and Android exports predate the loadout redesign (the packs shrank: no stems, 5.9 MB of loops); re-export
    before the next owner run.

## Everyday commands

```
bash tools/test.sh                                          # all headless tests + content build tests (about 1 min)
python tools/content/import_ableton.py content/imports/first_watch.json --check   # file an Ableton batch into the library (drop --check to write)
python tools/content/export_midi.py                         # MIDI loops + alternatives for missions 2 to 10 into midi_export/ (deterministic)
python tools/extract_openra.py --no-map                     # sprites from the owner's OpenRA content (allow-list NEEDED in the script)
python tools/extract_openra_sounds.py --check               # Red Alert sounds to assets/sfx (drop --check to write)
python tools/campaign/build_battlefield.py                  # regenerate the maps and battlefields (defense_02 and village_01)
RW_SECTION=none <godot> --headless --path . -s tools/autoplay.gd -- res://songs/m01_first_watch perfect 1.0 1   # harness without section taps
python tools/content/build.py                               # library (117 loops) + all ten packs, about 23 s; or name missions: level_05
python tools/balance_missions.py --loadout heavy --seeds 1 2 3 --jobs 4 > out.md   # trials with a preset of data/campaign/loadouts.json (default: "default"; about 80 s)
<godot> --headless --path . -s tools/autoplay.gd -- res://songs/m06_fortress perfect 1.0 1 loadout:heavy   # harness with a preset (or a JSON loadout); RW_LOADOUT=heavy does the same
python tools/content/render_list.py                         # rewrite docs/CONTENT_TO_RENDER.md
RW_MISSION=10 RW_SCENE=play RW_AUTOPLAY=perfect <godot> --path .    # scripted run in the real play screen, prints PERF
RW_MISSION=3 RW_SCENE=play RW_PRACTICE=1 <godot> --path .           # practice run (battlefield hidden)
RW_UNLOCK_ALL=1 <godot> --path .                            # every mission and option open for one run
RW_LEAD_IN=1.5 <godot> --path .                             # note speed override (0.6 to 2.0 s: time from screen top to pad)
<godot> --headless --path . --export-debug "Android" build/android/RhythmWarfare-debug.apk     # docs/EXPORT.md
```

`<godot>` is `C:\Users\joesa\Downloads\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe` on the
owner's machine. New `class_name` scripts need a `--import` before headless runs; `tools/test.sh` does that. In
Godot 4.5 `var x := dict["k"]` is a parse error: annotate the type. In this shell, long quoted Python in heredocs
fails when it contains apostrophes: write scripts to files.
