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

## Now (8 November, night)

`feature/one-pc` `d01bb628` (pushed): + the Bassment viewpoint fix (`test_trial` green: since A7 removed the edge beacons a
choice behind the camera has no tap target, so passages 2, 11, 28, 37 moved their viewpoints / raised the rope). All
filters green except `camera` 3 (the wiring step's rule). **Wiring step running** on `wip/wiring` (Opus, resumed after the
limit). After it: full suite, push, stage A's pause point (the owner plays `tools\dev\play_tracks.cmd --run` from
`MusicGame-onepc`); `main` only on the owner's word.

`feature/shared-contracts` `97c6f53a` (pushed): geography worlds (H1.6) merged: a world flagged `geography` is one scene
routing straight to other worlds' entry scenes; threshold = the route move's end; the threshold walk plays the polyline,
then the frame, the swap, the arrival (`docs/engine/GEOGRAPHY_WORLDS.md`, `tests/test_geography.gd`). **Follow-ups on
`wip/engine-geography`** (Opus): `commit_walk` (walk from the commit, built, 30628cc9) and ruling 39 (a geography guide's
tap commits at once; the window hold gives way to the walk) running. Merge both when the second reports.

`feature/doom-layout-worlds` (pushed after the Balcony suites): ALL EIGHT Doom worlds in the overlay (Warehouse, Booth, Bar,
Lounge, Dock, Underworld, Mothership, Balcony), 40 scenes, 0 rail problems, doom 6177 green; every scene still a 5-scene
stand-in world. **Next**: merge shared-contracts (geography) into env, then the REWIRE (Opus): each Doom world one
geography scene routing per the brief's table, stand-ins and return scenes deleted, test blocks updated, a real cut shot
(Warehouse → Bar). Polish list for stage D from the reports: Dock/Mothership/Underworld threshold shots stare at walls;
the Underworld's abyss does not read (needs a camera pitch on a waypoint); the Mothership's `void_top` haze hook; the
Balcony and Underworld under-exposed; no rain/sky anywhere; all guides procedural.

`feature/bedsit-raves` `8e438c54` (pushed): + the Space rave's activities staged in the room (spacewire) and A8b (the card
table in the day room: cards/chips as things, dealer and players as actors, bet/twist/stick/get-up in the pad slots).
All filters green. **Open owner decision**: A8b runs blackjack in `replace` mode (judging suspended while seated, no
wobble/fall, the run cannot end at the table) against decisions B6/B7 (`rhythm`); the pad slots cannot be both the rhythm
pads and the four card controls. Alternative if the owner keeps B6/B7: controls as in-world touches (deck = twist,
chips = bet, dealer = stick, door = up) with the pads staying rhythm. Next on this stream: the race (Opus), the
Magic/Dinos/Transport raves (no layouts yet), progression; the cloakroom queue reads semi-transparent (unexplained).

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
- 8 Nov night: one-pc `d01bb628`; shared-contracts `97c6f53a` (geography); doom-layout-worlds: eight worlds; bedsit-raves
  `8e438c54` (spacewire, A8b). Running: wiring, geography ruling 39.
