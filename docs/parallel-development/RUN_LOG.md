# RUN_LOG: the resume file for the long run

Read this first in a new session, then `git fetch --all`. The plan is `LONG_RUN_PLAN.md`; stage A's detail
is `TO_MAIN_PLAN.md`. Rewritten by the lead at every checkpoint. Times are Europe/London.

## Owner's answers (7 November 2026, 13:xx)

- WAD: supplied, `C:\Users\joesa\Documents\Cursor\MusicGame\doom II wads\doom2.wad` (IWAD header, 3,342
  lumps, 4.9 MB; copied to `C:\Users\joesa\rw-audio-work\doom\doom2.wad`, which is what `RW_DOOM_WAD`
  points at). Never in Git (`.gitignore`: `*.wad`, `/doom II wads/`). It carries no map geometry: a complete
  `DOOM2.WAD` is still wanted; the eight maps were traced from the ian-albert renders instead (owner approved
  the download; renders in `C:\Users\joesa\rw-audio-work\doom\renders\`, never in Git).
- Shape: confirmed (bedsit opening; four raves borrowing Mothership, Chill-out, Underworld, Dock
  geographies; eight Doom scenes behind a flag; legacy campaign kept).
- Order: stage B starts alongside stage A.
- Track: the Chase and Status remix of "Valley of the Shadows" (already imported).
- Push policy unchanged. Owner's words: "start the run and don't finish until everything altogether and
  done as new playable thing. Make sure to do art polish."
- 8 November: **ruling 38** (owner): every minigame is played in the same 2.5D world with the run's HUD, seamless
  transitions, no separate screen; contract 10; engine package A8; the card table converted later (A8b). The three
  activity agents were redirected to it.
- Later the same day: ruling 35 (stationary camera moments; no red/green rings, the artwork carries the
  state) and ruling 36 (the concept paintings are the bar; sprites like the guide crop,
  `art/reference/standard/`).

## START HERE (9 November): the run paused on the owner's word, 8 November late night

Say "Resume the run" and point the lead at this section. Everything below is pushed.

### What the owner can play now
- The campaign with all of stage A (one-pc, full suite green):
  `& "C:\Users\joesa\Documents\Cursor\MusicGame-onepc\tools\dev\play_tracks.cmd" --run`
- The eight Doom worlds as one geography with real doorway cuts (env):
  `& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd"` (`--scene doom_<id>` starts anywhere)
- The bedsit, the Space rave with its activities in the room, the card table, the race (play):
  `& "C:\Users\joesa\Documents\Cursor\MusicGame-play\tools\dev\play_bedsit.cmd" --rave space` (`--race space` goes straight to the race)
- Two stray Godot processes from a crashed race calibration (PIDs 11940 and 30000, `tools/race/calibrate_race.gd`) may still be
  alive; they hold `MusicGame-race`'s godot.sh lock. End them in Task Manager (or `Stop-Process -Id 11940,30000`).

### Branch heads (all pushed)
| Branch | Worktree | Head | State |
|---|---|---|---|
| `feature/one-pc` | `MusicGame-onepc` | `021706fc` + this log | stage A complete (Ward, Hospital, fixes, A7 Bassment, the viewpoint fix, the wiring step). Full suite 160,453 checks; 2 order-dependent failures (`test_heralds_view` wall unit case, `test_transition_fallback` memory) that pass alone. **Stage A pause point: the owner plays; `main` only on the owner's word.** |
| `feature/shared-contracts` | `MusicGame-contracts` | `f7762477` | A7, A8, geography (H1.6) + `commit_walk` + ruling 39, rulings 39/40 decided, rain (A9/H10) merged last. After the merge: weather 201 and story 48770 green; `run_`, `playtest`, `test_geography` were still running at the pause (`C:/Users/joesa/rw-audio-work/leadlogs/contracts_rain_*.log`): re-run them first thing. |
| `feature/doom-layout-worlds` | `MusicGame-env` | `589099a5` | eight one-scene geography worlds (8 scenes, 32 hotspots) routed per the brief; `tests/test_doom_cuts.gd` proves Warehouse→Bar→Warehouse. doom 2851, cuts 27, geography 189, run_ 16027, playtest 2938, story 48770 green. Contains `docs/briefs/DOOM_POLISH_BRIEF.md`. Does NOT yet have rain. |
| `feature/bedsit-raves` | `MusicGame-play` | `56a03f7a` | bedsit, Space rave with activities in the room, cloakroom, bar, card table (`replace`, ruling 40), spacewire, the race (merged last). After the race merge: race 1605, run_matrix 1755, space_rave 446 green; the rest of the play list not re-run since. |

### Paused agents (WIP commits pushed; nothing in `src/`; resume each with a FRESH Opus agent on the same worktree: brief + the notes below are its context)
| Worktree | Branch | Head | Where it stopped | Resume with |
|---|---|---|---|---|
| `MusicGame-polish-a` | `wip/polish-a` | `9726fc8f` | Warehouse steps 1,2,4,5,6 done (steel half-wall, wet floor, rig, 0.5 m plate under the ref viewpoint, crowd on the near half, all three guides cropped from the painting, `tools/doom/art/make_warehouse_art.py`), stopped at step 3: p50 0.25 / contrast 0.40 after two light passes, still just under. Bar and Lounge: art built (stone, cobbles, copper mains; marble, rug, coffered ceiling; foreground stool/counter, sofa/palms cropped) but NOT shot, NOT seen in engine, docs stale; thresholds moved (Bar right 2.5 m, Lounge ahead 3.6 m) so rail paths and `test_doom_views` are UNCHECKED. No tests run at all. | 1 lift Warehouse contrast/median; 2 shoot Bar (`shoot_bar.py`, new `RW_KEEP=<dir>` for `frame_check.py`) and Lounge, compare to paintings; 3 run doom, doom_cuts, rail_paths, run_, playtest, story + `check_rail_paths.gd`; 4 rewrite the three scene docs. Loose ends: unused `legs_below` in `make_guides.py`; stage guide's coat below the cut; Floor guide's hand on nothing; Warehouse/Lounge rooms still much larger than the paintings. |
| `MusicGame-polish-b` | `wip/polish-b` | `cc4ef476` | Dock only, between step 3 and 4: storm sky over the six open sectors, street 11 m longer north (ahead hold looks up the street), club passage to a lit door (left), right hold faces the furnace with the Underworld guide; 256 px wet tiles, furnace, bollards, pallets; lamp pools; all three guides cropped (`tools/doom/art/make_dock_crop.py`: Floor from the Dock painting, Mothership from the Booth painting, Underworld from `Rainy Dock of Three Paths-7.png`, seated behind crates). p50 0.22 → 0.22 (route_ahead 0.18; the painting itself is 0.14). `check_doom_map` OK. Not done: five differences not written down; floor gloss grainy mid-distance; no shots/doc; no tests. Balcony (p50 0.17) and Booth (0.23) untouched; Booth crop specs ready in the crop tool. | finish Dock exposure, reshoot, tests, `docs/doom/scenes/dock.md`; Balcony (moon sky + skyline, lower drop ceilings so the city shows, no crowd on the deck, alley at the stair foot, turn the cabin hold); then Booth. **Also**: once rain is merged into env, author `weather` into Dock/Balcony/Booth maps (`docs/engine/WEATHER.md`: map `weather {rain, wind, drips}`, sector `rain`/`wet`). |
| `MusicGame-polish-c` | `wip/polish-c` | `166c612c` | Underworld steps 1–6 done: abyss 5 m deep and much wider, lava lit as emissive (lamps grid, ambient 0.55, cliff feet glow), basalt kerb instead of chains, red cloud sky, gong/drums/bone chimes in view, warmer basalt + lantern posts; thresholds face a lit tunnel decal / a lit far path; Floor guide cropped from the Underworld painting, Dock guide cropped from the Mothership painting, Mothership guide procedural (improved). doom 2851/0/0 SCRIPT ERROR; `check_doom_map` OK; p50 0.17 → 0.23 (route_left 0.19), contrast 0.35 < 0.4. A full reshoot was running at the stop: `docs/shots/doom/underworld/contact.jpg`, `walk_up.txt` committed PARTWAY; walk strip and pitch −14 preview unfinished; scene doc and `underworld_scene.py` docstring stale. Mothership: new art drawn only (rib lattice ×3, void cliff tile, haze band decal, vault sky; `ms_wall_rib.png` overwritten, not reimported), nothing wired. | wire the Mothership (rib variants per ring piece, oval decals out, `ms_void_cliff` on the void step, haze band decals, low green pool lamps, `ms_sky` vault, empty crowd, threshold holds back from the hatch walls, Dock guide via the Underworld crop helper), `--import`, reshoot both scenes, run all filters + `check_rail_paths.gd`, update both docs. **Hooks reported**: the run's choice hold emits no glance, so a choice viewpoint has no field for a downward pitch (the Underworld's lava); `void_top` equals the void's floor when the void is split into wedges, so the depth haze is off (haze decal band is the workaround). |
| `MusicGame-raves` | `wip/play-raves` | `c6c8df29` | Shared `tools/story/rave_builder.py`, `rave_art.py`, `rave_people.py`; `build_space_rave.py` rebuilt on them with output unchanged; `make_bedsit.py` writes nodes/hotspots for every landed rave; `SpaceRaveHost` serves every theme; `tests/rave_theme_test.gd` shared body. **Magic complete** (test_magic_rave 555; space_rave 446, bedsit 187, cloakroom 3062, bar 362, activity_modes 149, playtest 3328, story 48896, all 0 SCRIPT ERROR). **Dinos complete** (test_dinos_rave 551; run_matrix 1862/0 after a setback fix in `make_bedsit.py`). **Transport NOT built** (dock tiles copied, trial rigs folder committed, nothing else). Other suites not re-run since Dinos. | FIRST merge `feature/bedsit-raves` into `wip/play-raves` (the race changed `make_bedsit.py` and `build_space_rave.py` after this agent forked: hangar real, `race.course`), regenerate, keep every theme's blocks in themes.json; then `build_transport_rave.py` (street forecourt→stage, cloakroom bay west, bar bay east, garage by the stage), RAVES/ORDER/LANDED entry, `tests/test_transport_rave.gd`, import, shoot, `play_bedsit.cmd --rave <any>` + LAUNCH.md, full test list. **Facts**: `BassKnobActivity` hard-codes the knob at world (0, −25.12) in a sector named `stage`, so every rave's stage is north; each rave's race entrance is a `<prefix>_race` placeholder node with a `hangar_view` pose (the race agent's `race_space` course serves all until per-theme courses: `tools/story/build_race.py --theme <x>`). |

### Lead's order of work on 9 November
1. Re-run the paused suites: contracts `run_ playtest test_geography`; play `run_ story playtest cloakroom bar bedsit activity_modes minigame blackjack`. Count SCRIPT ERROR lines. Fix or report.
2. Merge `feature/shared-contracts` (rain) into env and into play (`--no-ff`; expect no conflicts; nothing to regenerate). Push both.
3. Relaunch the four agents (fresh Opus, same worktrees, the table above pasted into each brief with the polish/raves brief path). The raves agent merges `feature/bedsit-raves` into its branch first.
4. Merge each polish branch into env when its filters are green: they touch disjoint scene files; `make_doom.py` untouched; `test_doom_views.gd` only inside their blocks; regenerate with `python tools/run/make_doom.py`; `--import`; doom/cuts/geography/run_/playtest/story; rail check. If `test_doom_views.gd` conflicts, rebuild from each side's blocks (never regex over markers).
5. Merge the raves into play when green; regenerate the bedsit; `--import`; full play list.
6. Bedsit progression check (brief section 10 against `tests/test_bedsit.gd`; per-rave flags, race results, facing, save version): a Sonnet task.
7. Stage D round 2 (Opus, from the lead's own look at every polish sheet), the independent review (Opus, fresh context, gaps not fixes, each branch against its brief), the LONG_RUN_PLAN stage D verification list, draft PRs for `feature/doom-layout-worlds` and `feature/bedsit-raves` (kept separate, not merged), `docs/HANDOVER.md`.
8. Stage E: the APK with the 61 tracks (never commit the packs). `main` only on the owner's word after the owner has played one-pc.

### Known gaps carried (for HANDOVER.md)
All Doom/rave/race art is placeholder until polish lands (round 1 crops guides from the paintings where big enough; the rest procedural); exposure under the rule in every Doom scene so far (p50 0.22–0.25, contrast ≤ 0.40); no phone run; no sfx for cues; Gospel p5; A7's door readability; the Floor's four gates hidden from the booth in the route window (placement pass); 18 hidden herald samples and 5 unseen ways back pinned in `KNOWN_HIDDEN`/`KNOWN_BACK_UNSEEN`; race entry is a cut not a drive-in; race position not saved; cloakroom queue reads semi-transparent (unexplained); Mothership `void_top` haze hook; no downward-pitch field at a choice hold; `test_trial` prints one "Parse JSON failed" line (not a failure); two order-dependent failures in the one-pc full run.

### Lessons that save time
Resolve `make_doom.py`/`test_doom_views.gd` merges by rebuilding from each side's blocks, never by regex over conflict markers (twice burnt). Run `--import` in every fresh worktree and after merging new assets ("sheet not found" failures were un-imported sheets). The runner prints "0 failures" on a parse error: always count SCRIPT ERROR lines. `git clean -fq` stray untracked `.import`/`.uid` files before a merge that brings the same ones. The full one-pc suite takes about 25 minutes: background only. Python heredocs in Git Bash: write the file with the Write tool, not a quoted heredoc with Windows paths.

## Checkpoint history

- 7 Nov 13:xx: phase 0 done. Five WIP checkpoints committed and pushed; `wip/art-a6` and `wip/art-w7`
  pushed. WAD copied outside Git and ignored.
- 7 Nov evening: one-pc `c16aac62` (A6, W7, Hell, pins, N2.5, Spaceship, Hell fix); shared-contracts
  `04cd0d7b`; doom-layout-worlds `8900f4cf`; bedsit-raves `04cd0d7b`. Full suite at `db53b4d3`: 149,354
  checks, 1 failure (fixed since).
- 7 Nov night: one-pc `b35c2f56` (W6, Ward; red: 4 heralds_view, 2 blackjack, see above);
  shared-contracts `7cfa6cc4`; doom-layout-worlds `f89d96f5`; bedsit-raves `9de607c6`.
- 8 Nov midday: one-pc `15dba656`; shared-contracts `8db13e8f` (A7, A8); doom-layout-worlds `a3ae9a16` (Booth);
  bedsit-raves `e426ae1b` (cloakroom, bar, Space rave, bedsit fix, A8).
- 8 Nov evening: doom-layout-worlds `b6be9af6` (Bar, Lounge: four worlds, all filters green); eight agents running
  (wiring, geography, four wave-2 scenes, spacewire, card table).
- 8 Nov night: one-pc `d01bb628`; shared-contracts `97c6f53a` (geography); doom-layout-worlds: eight worlds; bedsit-raves
  `8e438c54` (spacewire, A8b). Running: wiring, geography ruling 39.
- 8 Nov late night (run paused by the owner): one-pc 021706fc (wiring, full suite green); shared-contracts f7762477 (rain); doom-layout-worlds 589099a5 (eight geography worlds, cuts); bedsit-raves 56a03f7a (race). Paused mid-work and pushed: wip/polish-a 9726fc8f, wip/polish-b cc4ef476, wip/polish-c 166c612c, wip/play-raves c6c8df29.

## 9 November (the owner's clock: still 8 Nov local, late): the run resumed

- Checked every worktree in step with its remote; no stray Godot processes left; only untracked `.uid`/`.import` files.
- Contracts rain suites from last night all green (playtest 2993, test_geography 189, 0 SCRIPT ERROR): step 1 for contracts done.
- Merged `feature/shared-contracts` f7762477 (rain) `--no-ff` into env → `6addc102` and play → `6001fa7d`, both imported, both pushed.
- Merged env into the three polish branches: `wip/polish-a` a40eeff6, `wip/polish-b` eeba725e, `wip/polish-c` 6725235a (clean).
  `wip/play-raves` ← `feature/bedsit-raves` conflicts in `tools/run/make_bedsit.py`: aborted, left to the raves agent (it has both sides' context).
- Play list re-running on the merged play branch in the background (`leadlogs/play_rain_<filter>.log`).
- Relaunched the four agents fresh (Opus) on their worktrees with the START HERE table rows as context; a Sonnet read-only
  progression gap check on play; a Sonnet APK agent in a new worktree `MusicGame-apk` on `wip/apk` from `feature/one-pc`.
- Bedsit progression gap check (read-only, against brief section 10): facing, theme, per-theme `raves.<theme>.{bass_fixed,cloakroom_done,bar_done,race{wins,runs,best}}`, puzzle scoping, new-run reset, save v2→v3 migration all implemented and tested (`tests/test_bedsit.gd`, `test_run_progress_v3.gd`, `test_contracts.gd`, `test_space_rave.gd`). GAPS carried: (1) no test that the opening finishes after one rave; (2) `BedsitNav.press` is called by no tap (LAUNCH.md names hook H5.5 for the dispatcher), so a facing reaching the save from a real tap is unproven; (3) the three activities are exercised in no non-space theme until the raves land; (4) LAUNCH.md:55 (press never stamps v3) may be stale now `RunProgress` loads v3. Race records persist across new runs as a career record (not in the brief; keep). Follow-up for the raves agent after Transport: (1) and (3).
- Play list on `feature/bedsit-raves` 6001fa7d (rain merged), all 0 failures / 0 SCRIPT ERROR: run_ 16374, story 48896, playtest 3224, cloakroom 3062, bar 362, bedsit 197, activity_modes 149, minigame 251, blackjack 10611, weather 201, test_geography 189, race 1605, space_rave 446. Env's list on 6addc102 running (`leadlogs/env_rain_<filter>.log`).
- Env list on `feature/doom-layout-worlds` 6addc102 (rain merged), all 0 failures / 0 SCRIPT ERROR: doom 2851, doom_cuts 27, test_geography 189, weather 201, run_ 16025, playtest 2971, story 48770; rail check 8 scenes, 0 problems. Both integration branches are clean bases for the polish and raves merges.
- **Stage E done up to the phone** (Sonnet agent, `wip/apk` in `MusicGame-apk`, merged `--no-ff` into one-pc 93779219): the 61 packs (4.6 GB on disk, Ogg ~500 kbps plus 684 MB of previews/reports) re-encode with `tools/audio_import/build_android_packs.py` (ffmpeg libvorbis q4, 48 kHz stereo, lengths identical) to a 1,027 MB bundle in the git-ignored `/track_packs/` (each stem with an `importer="keep"` `.import`); the Android preset includes `track_packs/*/track.json`; `RunTrackScenes.packs_root` falls back to `res://track_packs` when `RW_TRACKS_DIR` is unset and `user://track_packs` is absent. Full debug APK `MusicGame-apk/build/android/RhythmWarfare-debug.apk` 1.23 GB, export exit 0, 256 stems + 61 track.json in the zip. run_ 16705 / playtest 2982 green with the bundle present. Lead's fix fa43278c: the bundled `res://` path stays `res://` (a globalized res:// path is not a folder inside an APK); track 3163, run_ 16706, playtest 2982 green; re-export requested. NOT done: nothing on a phone (install, playback, latency, memory); q4 not auditioned; no release keystore. Plan: `docs/APK_61_TRACKS.md`.
- APK re-exported after the fix (`wip/apk` 99500c6c, merged into one-pc 16880b9e): same 1.23 GB, exit 0, 256 stems + 61 track.json listed; new `tests/test_run_tracks_bundled.gd` (4 checks: `packs_root()` returns `res://track_packs` when nothing else is set, 61 pack folders each with track.json, `TrackPack.load_pack` accepts one); track 3167, run_ 16705 green. Stage E stands at "done up to the phone".
- Raves agent reported (`wip/play-raves` fa07f2f0): the race merge reconciled in `make_bedsit.py` (the hangar is a real activity scene for any theme with `content/races/<theme>.json`, Space only today; `hotspots/space_rave.json` byte-identical to the race side); Transport rave built on the shared builder (wet forecourt → tracks → depot hall; stage north, left-luggage bay west, ticket office east, garage by the stage; rain on the forecourt; all its props and people placeholders, said so); `play_bedsit.cmd --rave magic|dinos|transport`; `tests/test_transport_rave.gd` 551; `test_cloakroom` fixed (dinos' own layout). Full play list green (17 filters, 0 failures, 0 SCRIPT ERROR: run_ 16681, story 48896, playtest 3547, cloakroom 3062, bar 362, bedsit 182, activity_modes 149, minigame 251, blackjack 10611, race 1605, space/magic/dinos/transport_rave 446/555/551/551, run_matrix 1899, weather 201, test_geography 189). Its stand-in ending needed all four raves: **ruling 41** (contracts `LEAD_RULINGS.md`) replaces it with "any one rave's three activities"; the agent is changing the gate and adding the test; merge into play after that.
