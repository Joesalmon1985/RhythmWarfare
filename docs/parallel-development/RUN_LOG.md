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

## Now (8 November, evening)

`feature/one-pc` `15dba656` (pushed): Ward, Hospital, both fix passes, A7 merged; filters green except `camera` 3 (herald
looks during door walks / a 2.4 m room: the wiring step's engine rule). **Wiring step running** on `wip/wiring`
(`MusicGame-wiring`, Opus). After it: the full suite, push, stage A's pause point (the owner plays
`tools\dev\play_tracks.cmd --run` from `MusicGame-onepc`); `main` only on the owner's word.

`feature/shared-contracts` `8db13e8f` (pushed): A7 and A8 merged (dynamic things, people states, feedback, the pad-slot
morph: ruling 38, contract 10), all filters green. **Geography worlds (H1.6) running** on `wip/engine-geography`
(`MusicGame-geo`, Opus): a world flagged `geography` is one scene that routes straight to other worlds' entry scenes, the
threshold defaults to the route move's end, the threshold walk plays the route polyline, then the frame, the swap and the
arrival. When it lands: merge into shared-contracts, then into env, and a generator change deletes the Doom stand-ins.

`feature/doom-layout-worlds` `b6be9af6` (pushed): Warehouse, Booth (`doom_booth`), Copper Bar (`doom_bar`) and Chill-out
Lounge (`doom_lounge`) as four worlds, 20 scenes, 0 rail problems; doom 3631, rail_paths 652, run_ 16029, playtest 2993,
story 48770, all green. **Wave 2 running** (Sonnet, brief `docs/briefs/DOOM_WAVE2_BRIEF.md`): `wip/env-balcony` (MAP15,
renames the Warehouse's `doom_balcony` stand-in to `doom_warehouse.balcony`), `wip/env-dock` (MAP13), `wip/env-mothership`
(MAP11), `wip/env-underworld` (MAP29). Merge order at the end: each adds a two-line block to `make_doom.py`, a block at
the end of `test_doom_views.gd` and a LAUNCH.md section; regenerate the overlay after every merge (never hand-merge
`content/run/doom/*`). Lesson from the Bar and Lounge merges: resolve `make_doom.py` and `test_doom_views.gd` by
rebuilding from the two sides' files (the Warehouse part + each block in order), not by regex over conflict markers.

`feature/bedsit-raves` `e426ae1b` (pushed): the bedsit, the Space rave, the cloakroom, the bar, the bedsit fix, A7, A8;
all filters green incl. run_matrix (the activity tests assert the pad-slot morph). **Running**: `wip/play-spacewire`
(`MusicGame-spacewire`: generator keeps the themes.json blocks, the three activities placed in the Space rave through A8,
real shots) and `wip/play-cardtable` (`MusicGame-cardtable`, Opus, A8b: the card table as in-room staging). Next: the
race (Opus), the Magic/Dinos/Transport raves, progression.

Known gaps carried: H3.1 choice viewpoint framing, H9.2/H9.3, no sfx files for cues, all Doom/rave/activity art placeholder
(stage D), no phone runs, Gospel p5, A7's door-readability finding (lamp, spill, closer choice viewpoint).

## Worktrees and agents

| Worktree | Branch | State |
|---|---|---|
| `MusicGame-onepc` | `feature/one-pc` | integration, stage A |
| `MusicGame-contracts` | `feature/shared-contracts` | integration, engine |
| `MusicGame-env` | `feature/doom-layout-worlds` | integration, env |
| `MusicGame-play` | `feature/bedsit-raves` | integration, gameplay |
| `MusicGame-wiring` | `wip/wiring` | wiring running (Opus) |
| `MusicGame-geo` | `wip/engine-geography` | geography worlds / H1.6 running (Opus) |
| `MusicGame-env-balcony`, `-dock`, `-mothership`, `-underworld` | `wip/env-*` | wave 2 running (Sonnet) |
| `MusicGame-spacewire` | `wip/play-spacewire` | running |
| `MusicGame-cardtable` | `wip/play-cardtable` | A8b running (Opus) |
| `MusicGame-engine`, `-props` | `wip/engine-choice`, `wip/engine-props` | A7, A8 merged |
| `MusicGame-env-bar`, `-booth`, `-chill`, `-envwh`, `-envtools` | `wip/env-*` | merged |
| `MusicGame-space`, `-cloakroom`, `-bar`, `-bedsit` | `wip/play-*` | merged |
| `MusicGame-music`, `-import`, `-graph`, `-herald`, `-narr`, `-art`, `-docs` | stage A wip branches | merged, to remove |

## Next action for the lead

1. Merge the wiring step into `feature/one-pc`; full suite; push; stage A pause point (the owner plays).
2. Merge geography (H1.6) into `feature/shared-contracts`, then into env and play; merge wave 2 into env (regenerate the
   overlay each time); then an env agent rewires the eight Doom worlds as geography worlds (stand-ins deleted) and the
   routing table of the brief becomes the real cuts.
3. Merge spacewire and A8b into `feature/bedsit-raves`; then the race, the other three raves, progression.
4. Stage D (Opus polish to ruling 36 on every scene, review, verification, draft PRs), stage E (APK with the 61 tracks).

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
