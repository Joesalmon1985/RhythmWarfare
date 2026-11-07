# RUN_LOG: the resume file for the long run

Read this first in a new session, then `git fetch --all`. The plan is `LONG_RUN_PLAN.md`; stage A's detail
is `TO_MAIN_PLAN.md`. Rewritten by the lead at every checkpoint. Times are Europe/London.

## Owner's answers (7 November 2026, 13:xx)

- WAD: supplied, `C:\Users\joesa\Documents\Cursor\MusicGame\doom II wads\doom2.wad` (IWAD header, 3,342
  lumps, 4.9 MB; copied to `C:\Users\joesa\rw-audio-work\doom\doom2.wad`, which is what `RW_DOOM_WAD`
  points at). Never in Git (`.gitignore`: `*.wad`, `/doom II wads/`).
- Shape: confirmed (bedsit opening; four raves borrowing Mothership, Chill-out, Underworld, Dock
  geographies; eight Doom scenes behind a flag; legacy campaign kept).
- Order: stage B starts alongside stage A.
- Track: the Chase and Status remix of "Valley of the Shadows" (already imported).
- Push policy unchanged. Owner's words: "start the run and don't finish until everything altogether and
  done as new playable thing. Make sure to do art polish."

## Now (7 November, evening)

`feature/one-pc` `c16aac62`: merged today A6, W7, Hell, N2.5 returns, Spaceship entrances, the pinned tests made
data-driven, the Hell clearance fix. Full suite at `db53b4d3`: 149,354 checks, 1 failure (fixed since). Open: Ward
(spacing pass), Hospital (finishing), W6 Gospel (daylight pass). Then the shared wiring step and the Floor's entrances.

`feature/shared-contracts` `04cd0d7b` (pushed): the nine contracts, fixtures, the stem lock, the renderer and rail
extension (steps, voids, railings, clipped visibility, polyline moves, holds, `check_rail_paths`), the art
standard images; `wip/engine-host` (Opus) is building hooks H5, H6, H3, H1, H7, H4 on top.

`feature/doom-layout-worlds` `8900f4cf` (pushed): the conversion chain, all eight maps traced from the renders
(approximate), the Warehouse pilot (scene behind `RW_DOOM_WORLDS=1`, `tools\dev\play_doom_worlds.cmd`); the pilot's
layout pass runs on `wip/env-warehouse`. The supplied WAD has no map geometry: a complete `DOOM2.WAD` is still wanted.

`feature/bedsit-raves` `04cd0d7b` (pushed): `wip/play-bedsit` builds the room, the path and the four facings.

## Earlier today

Stage: **A phase 1 and B1/B2 in parallel**, 7 November afternoon.

Merged into `feature/one-pc` today: A6 (decals), W7 (Squadron), N2.4 Hell. Filters green except the two
pinned tests (`test_heralds.gd` ENTRANCES, `test_narrative_run.gd` fixture rows), being fixed on
`wip/narr-pins` (worktree `MusicGame-pins`). Housekeeping done: 8 stale worktrees and 32 merged local
branches removed; `feature/story-warehouse-music-test` kept (its upstream differs; owner's call).

Owner's direction of 7 November (ruling 35): more stationary camera moments; the red/green rings replaced
by the artwork's own state everywhere. In the contracts (rail holds, contract 9 choice states); package A7
to follow for the legacy worlds.

Running agents: N2.5 returns (`MusicGame-herald`), N2.4 Ward (`MusicGame-import`), env tools / WAD
converter (`MusicGame-envtools`, `wip/env-tools`), contracts (`MusicGame-contracts`,
`wip/engine-contracts`), renderer and rail extension (`MusicGame-engine`, `wip/engine-render`, Opus),
pinned tests (`MusicGame-pins`). Not yet resumed: N2.4 Hospital (`MusicGame-music`), N2.4 Spaceship
(`MusicGame-graph`), W6 Gospel (`MusicGame-narr`).

Last pause point reached: none yet.

## Branches and their last pushed commit

| Branch | Worktree | Commit | State |
|---|---|---|---|
| `feature/one-pc` | `MusicGame-onepc` | see `git log` | integration for stage A |
| `wip/narr-n2-4-underworld` | (none) | `3c16b4c9` | finished, to merge |
| `wip/narr-n2-4-mothership` | `MusicGame-graph` | `006f910d` WIP | agent to resume |
| `wip/narr-n2-4-ward` | `MusicGame-import` | `961561db` WIP | agent to resume (visibility fixes) |
| `wip/narr-n2-4-hospital` | `MusicGame-music` | `48d3610a` WIP | agent to resume |
| `wip/narr-n2-5` | `MusicGame-herald` | `1cfd7b8f` WIP | agent to resume |
| `wip/art-a6` | `MusicGame-art` | `bae5eca0` | report, review, merge |
| `wip/art-w6` | `MusicGame-narr` | `4b936ba0` WIP | agent to resume (daylight) |
| `wip/art-w7` | `MusicGame-docs` | `18da401b` | report, review, merge |

Stage B branches: see the table in `LONG_RUN_PLAN.md`; created when stage B starts (below).

## Next action for the lead

1. Resume the stage A agents by message (at most four at once with the stage B agents counted).
2. Create `feature/shared-contracts`, `feature/doom-layout-worlds`, `feature/bedsit-raves` from
   `feature/one-pc`; worktrees `MusicGame-env`, `MusicGame-play`, `MusicGame-engine`.
3. Write `CONTRACTS.md`; start the env tools agent (WAD reader) and the engine owner.

## Checkpoint history

- 7 Nov 13:xx: phase 0 done. Five WIP checkpoints committed and pushed; `wip/art-a6` and `wip/art-w7`
  pushed. WAD copied outside Git and ignored.
