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

## Now (8 November, morning)

`feature/one-pc` `7d6cc45d` (pushed): the Hospital (N2.4) merged on top of the Ward. Red right now, all assigned: `heralds_view`
4 (the Ward's `ward.corridor`, `ward_late.dorm` route windows), `camera` 4 (ward arrival, ward.corridor from art and dorm,
hospital_late.quiet), `blackjack` 2 (fixed by A7, lands with the shared-contracts merge). Fix passes running: `wip/narr-ward-fix`
(`MusicGame-import`), `wip/narr-hospital-fix` (`MusicGame-music`: quiet room, re-shoot against the new art; the day-room
gate's crowd is fixed by A7). Then: merge `feature/shared-contracts` (A7) into one-pc, the shared wiring step, the Floor's
entrances, the full suite.

`feature/shared-contracts` `6b7fdf48`: **A7 merged** (no rings anywhere: a choice's state is its own artwork, `ChoiceState`,
`ChoiceShow`, `content/run/choice_show.json`, every hotspot row declares `show`, heralds use the crowd that owns their sector).
A7's own finding for the polish: at the Warehouse opening's distance a door does not yet read as available vs selected (the
lamp is a few pixels, the spill faint); needs a bigger lamp/stronger spill and the choice viewpoint holding closer (H3.1).
Filters running. A8 (`wip/engine-props`, `MusicGame-props`, Opus) building the dynamic things, people states, feedback and
the pad-slot morph (ruling 38).

`feature/bedsit-raves` `a89f29ba`: the cloakroom and the Space rave merged (the bar `wip/play-bar` next). Known red: `run_matrix`
76 ("bedsit leads to bedsit", the placeholder raves loop home) being fixed on `wip/play-bedsit-fix`. The activities are
staged per ruling 38 as data (things, people, feedback) and need A8 to draw; their shots are data previews, not the stage.

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
| `MusicGame-engine` | `wip/engine-choice` | A7 merged |
| `MusicGame-props` | `wip/engine-props` | A8 running (Opus): dynamic things, people states, feedback, pad-slot morph (ruling 38, contract 10) |
| `MusicGame-music` | `wip/narr-hospital-fix` | Hospital fix running |
| `MusicGame-import` | `wip/narr-ward-fix` | Ward fix running |
| `MusicGame-space` | `wip/play-space` | merged |
| `MusicGame-cloakroom` | `wip/play-cloakroom` | merged |
| `MusicGame-bar` | `wip/play-bar` | to merge |
| `MusicGame-bedsit` | `wip/play-bedsit-fix` | run_matrix fix running |
| `MusicGame-envwh` | `wip/env-warehouse-rail` | merged |
| `MusicGame-envtools` | `wip/env-tools` | merged |
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
- 7 Nov late: shared wiring on `wip/wiring` (from one-pc `b74aa327`). The herald look stops short of a near wall (camera 0 failures, no gate moved); four hub links and 31 ways back
  (`<scene>.to_hub`) with a `RunData` hub-route rule and `max_hotspots` 10 on the five hubs; the paths' 5 restarts, 2 second routes and 7 back routes (no path scene under three
  destinations); the Bassment's own way back from 49 passages (7 have no spot their camera shows); the window look weighs entrances 2 and ways back 0.5; the wall test in
  `tests/test_heralds_view.gd` (18 hidden entrance samples and 5 unseen ways back pinned as `KNOWN_HIDDEN` / `KNOWN_BACK_UNSEEN`: placement work for the location packages);
  the Floor's own four entrances (sheet `docs/shots/narrative/n2_4_warehouse/floor_gates_sheet.jpg`: lit and framed in the opening, hidden behind the booth's rails in the route
  window). Graph target 20 of 20 cells, `check_hotspots` 0 errors.
