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

## Now (7 November, night; the lead's usage limit was reached here: agents may still be running or have reported into their worktrees, check each worktree's `git log` and the branch table)

`feature/one-pc` `b35c2f56`: the Ward (N2.4) merged. Merged today in order: A6, W7, Hell, pins, N2.5 returns,
Spaceship, Hell clearance fix, W6 Gospel daylight, Ward. **Red on one-pc right now**: `test_heralds_view` 4
failures (`ward.corridor.enter_squadron`, `ward_late.dorm.enter_gospel`: 0% of the route window, because the
one-pc camera re-aim of `run.json` and the N2.5 returns landed after the Ward forked; green on the Ward branch
itself) plus `test_camera_clearance` 3 failures (ward arrival, ward.corridor from art and dorm: herald looks onto walls), same cause, being fixed on `wip/narr-ward-fix` (worktree `MusicGame-import`, the Ward agent resumed); `test_blackjack`
2 failures (edge-beacon touch stacks, `hotspot_view.gd:273`) and one culled gate in `ward_late.treat`, with A7
(`wip/engine-choice`, `MusicGame-engine`, Opus). Still open on stage A: Hospital N2.4 (`MusicGame-music`,
running), then the shared wiring step and the Floor's entrances, then the full suite.

`feature/shared-contracts` `7cfa6cc4` (pushed): the nine contracts, fixtures, the stem lock, the renderer and rail
extension, the gameplay hooks (activity modes, save v3, holds, relaxed node, threshold walk, stem unlock), the
art standard images.

`feature/doom-layout-worlds` `f89d96f5`: the conversion chain, all eight maps traced (approximate), the Warehouse
pilot on the new rail (via polylines, holds, choice viewpoint held 8 bars, railings, clipped visibility, 0 rail
problems on the five Doom scenes). Not done there: the exit walks (ahead/left/right door walks) still jump to the
next scene's arrival; `rail.routes` is checked and shot, not played. Filters after the merge: see the checkpoint
line below.

`feature/bedsit-raves` `9de607c6` (pushed): the bedsit (room, path, four facings, `RW_BEDSIT=1`,
`tools\dev\play_bedsit.cmd`, placeholder rave nodes). Running on top, one agent each (Sonnet):
`wip/play-space` (`MusicGame-space`: the Space rave on the Mothership geography, hub choice viewpoint, stage
route, the bass-knob puzzle on `lock_stems`/`unlock_stem_at`), `wip/play-cloakroom` (`MusicGame-cloakroom`:
same/different in replace mode, `src/minigames/cloakroom/`), `wip/play-bar` (`MusicGame-bar`: recipe memory,
`src/minigames/bar/`). Then the race, the other three raves, progression.

## Worktrees and agents

| Worktree | Branch | State |
|---|---|---|
| `MusicGame-onepc` | `feature/one-pc` | integration, stage A |
| `MusicGame-contracts` | `feature/shared-contracts` | integration, engine |
| `MusicGame-env` | `feature/doom-layout-worlds` | integration, env |
| `MusicGame-play` | `feature/bedsit-raves` | integration, gameplay |
| `MusicGame-engine` | `wip/engine-choice` | A7 running (Opus) |
| `MusicGame-props` | `wip/engine-props` | A8 running (Opus): dynamic things, people states, feedback, pad-slot morph (ruling 38, contract 10) |
| `MusicGame-music` | `wip/narr-n2-4-hospital` | Hospital running |
| `MusicGame-import` | `wip/narr-ward-fix` | Ward fix running |
| `MusicGame-space` | `wip/play-space` | running |
| `MusicGame-cloakroom` | `wip/play-cloakroom` | running |
| `MusicGame-bar` | `wip/play-bar` | running |
| `MusicGame-envwh` | `wip/env-warehouse-rail` | merged |
| `MusicGame-envtools` | `wip/env-tools` | merged |
| `MusicGame-bedsit` | `wip/play-bedsit` | merged |
| `MusicGame-graph`, `-herald`, `-narr`, `-art`, `-docs` | stage A wip branches | merged, to remove |

## Next action for the lead

1. Merge the Ward fix into `feature/one-pc`; merge Hospital when it reports; merge A7 into
   `feature/shared-contracts` and then into the three streams.
2. The shared wiring step on one-pc (hub-to-hub links, `to_hub` routes, `max_hotspots`, back/restart routes,
   the Bassment return, the window look including returns, the wall test in `heralds_view`); the Floor's
   entrances; the full suite; stage A pause point (the owner plays).
3. Stage C waves: the seven remaining Doom scenes (Bar, Booth, Lounge; Balcony, Dock, Mothership,
   Underworld), the race and the other three raves; then stage D (Opus polish to ruling 36, review,
   verification, draft PRs) and stage E (APK).

## Checkpoint history

- 7 Nov 13:xx: phase 0 done. Five WIP checkpoints committed and pushed; `wip/art-a6` and `wip/art-w7`
  pushed. WAD copied outside Git and ignored.
- 7 Nov evening: one-pc `c16aac62` (A6, W7, Hell, pins, N2.5, Spaceship, Hell fix); shared-contracts
  `04cd0d7b`; doom-layout-worlds `8900f4cf`; bedsit-raves `04cd0d7b`. Full suite at `db53b4d3`: 149,354
  checks, 1 failure (fixed since).
- 7 Nov night: one-pc `b35c2f56` (W6, Ward; red: 4 heralds_view, 2 blackjack, see above);
  shared-contracts `7cfa6cc4`; doom-layout-worlds `f89d96f5`; bedsit-raves `9de607c6`.
