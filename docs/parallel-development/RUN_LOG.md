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

## Now (8 November, midday)

`feature/one-pc` `b74aa327` (pushed): Ward, Hospital, both fix passes and `feature/shared-contracts` (A7: no rings) merged.
Filters green (choice, hotspot, heralds_view, herald, blackjack, returns, interaction, narrative, story, run_, playtest);
the only red is `camera` 3 (ward.corridor x2, hospital_late.quiet: a herald look swinging onto a wall during a door walk /
in a 2.4 m room), an engine rule in the wiring step. **Wiring step running** on `wip/wiring` (`MusicGame-wiring`, Opus):
hub-to-hub links and ways back, back/restart routes and the Bassment return, the herald-look clearance rule, the window
look including returns, the wall test in heralds_view, the Floor's four entrances, then the full suite. After it: stage A's
pause point (the owner plays `tools\dev\play_tracks.cmd --run` from `MusicGame-onepc`).

`feature/shared-contracts` `6b7fdf48` (pushed): A7 merged, all filters green. A8 running (`wip/engine-props`,
`MusicGame-props`, Opus): dynamic things, people states, feedback, the pad-slot morph (ruling 38, contract 10), aligned to
what the three activities used (`WorldThings` with piece_on/off/pulse; `pictogram`/`shape`+`color` controls; frown,
raise_glass states; `thing_screen_point` for map things too).

`feature/doom-layout-worlds` `bb1b7ccb` (pushed): Warehouse pilot on the new rail + A7; filters green. **Stage C wave 1
running**: `wip/env-bar` (MAP02), `wip/env-booth` (MAP04), `wip/env-chill` (MAP08 lounge), worktrees `MusicGame-env-bar/
-booth/-chill`, Sonnet, each on the pilot's pipeline. Wave 2 after: Balcony, Dock, Mothership, Underworld.

`feature/bedsit-raves` `3d1d4c01` (pushed): the bedsit, the Space rave (hub hold, bass knob), the cloakroom, the bar, the
bedsit fix (placeholder raves end the path; the run matrix accepts a relaxed node) + A7; all filters green incl.
run_matrix. The activities are staged as data (things, people, feedback, pad-slot controls) and draw nothing until A8 lands;
`tools/run/make_bedsit.py --bedsit` rewrites themes.json WITHOUT the cloakroom and bar blocks (restore from Git after a
regenerate, or teach the generator to keep them: a hook for the rave wave). Next on this stream after A8: the race, the
Magic/Dinos/Transport raves, the activities placed in the Space rave, A8b (the card table converted to ruling 38).

## Worktrees and agents

| Worktree | Branch | State |
|---|---|---|
| `MusicGame-onepc` | `feature/one-pc` | integration, stage A |
| `MusicGame-contracts` | `feature/shared-contracts` | integration, engine |
| `MusicGame-env` | `feature/doom-layout-worlds` | integration, env |
| `MusicGame-play` | `feature/bedsit-raves` | integration, gameplay |
| `MusicGame-engine` | `wip/engine-choice` | A7 merged |
| `MusicGame-props` | `wip/engine-props` | A8 running (Opus): dynamic things, people states, feedback, pad-slot morph (ruling 38, contract 10) |
| `MusicGame-music` | `wip/narr-hospital-fix` | merged |
| `MusicGame-import` | `wip/narr-ward-fix` | merged |
| `MusicGame-wiring` | `wip/wiring` | wiring running (Opus) |
| `MusicGame-env-bar`, `-booth`, `-chill` | `wip/env-bar`, `-booth`, `-chill` | wave 1 running |
| `MusicGame-space` | `wip/play-space` | merged |
| `MusicGame-cloakroom` | `wip/play-cloakroom` | merged |
| `MusicGame-bar` | `wip/play-bar` | merged |
| `MusicGame-bedsit` | `wip/play-bedsit-fix` | merged |
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
