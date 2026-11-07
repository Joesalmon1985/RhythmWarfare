# The long run: to `main`, then the Doom worlds and the bedsit opening (7 November 2026)

One plan for everything the owner has asked for, run as a single long job across several days and sessions.
It is built to be stopped at any point (the usage limit, or the PC switched off) and picked up again from
Git and one resume file. Nothing in it starts until the owner has read it and said go.

## The end goals

1. **A `main` that carries everything built so far.** The five-location campaign (Warehouse hub, Hospital,
   Mental Hospital, Spaceship, Hell), the four quests, heralds and lit gates at every entrance, ways back
   from every quest, the DJ-style transitions over the owner's 61 tracks, the art packages, camera clearance,
   all verified by the full suite and by the owner's own play and listen. `main` moves only on the owner's
   word. (`TO_MAIN_PLAN.md` is the detail; it is stage A here.)
2. **Eight explorable environments on Doom II geography**, each matching one of the owner's concept
   images, walked on the first-person rail while the rhythm game plays, with three guide characters per
   scene as the destinations (ahead, left, right) and "stay" at the bottom, and the exact eight-scene
   routing from the brief. Behind a feature flag, launchable on its own and as the whole set. Branch
   `feature/doom-layout-worlds`, pushed, not merged.
3. **A new opening: the bedsit.** One room seen in four directions; each direction's forward threshold
   leads to one of four raves (Space, Magic and unicorns, Dinosaurs, Transport). Every rave has the same
   three activities (fix the bass knob on the stage, work the cloakroom, serve drinks at the bar), a way
   into street racing, and a way home. The cloakroom and bar replace rhythm play with their own controls
   and suspend judging; racing keeps the pads and adds four driving regions. Progress is explicit, saved,
   per rave. Branch `feature/bedsit-raves`, pushed, not merged.
4. **Shared engine and contracts, owned once.** Scene entry and exit, theme selection, rail destinations
   and arrival poses, activity entry/result/exit, input ownership and rhythm participation, puzzle
   progression, bass unlocking through the stem transport, race rendering. One branch
   (`feature/shared-contracts`) both streams merge from, one owner (the lead).
5. **The Android APK with the 61 tracks bundled**, measured on a phone if one is available, at the end.
6. **An honest record** of what was implemented, what was looked at in the running game, what was tested,
   and what is still missing, in `docs/HANDOVER.md`.

## What the survey found (7 November)

- Concept art: 16 PNGs in `C:\Users\joesa\Documents\Cursor\MusicGame\Concept art`: the eight the brief
  names and a second variant of each scene ("Copper Bar Crossroads", "Midnight dance hall with three
  guides", "Mothership atrium", "Mustard lounge with three new paths", "Rain-Slick Rooftop Crossroads",
  "Rainy DJ Booth and Three Visitors", "Rainy Dock of Three Paths", "Three Visitors in the Basalt
  Underworld"). The named eight are the targets; the variants are secondary references (lighting, props,
  the guides' costumes from another angle). The guides painted in each image already match the routing
  table (the Mothership: a horned drummer ahead for the Underworld, a DJ on the left for the Booth, a man in
  a green raincoat on the right for the Dock).
- **No `doom2.wad` anywhere on the PC** and no WAD reader in the project. Unless the owner supplies one
  (copied outside Git, to `C:\Users\joesa\rw-audio-work\doom\doom2.wad`), the geography is reconstructed
  from the ian-albert map renders and is called *approximate* throughout. The converter is written to take
  a WAD when one appears, so the approximate maps can be replaced later without redoing the scenes.
- **"Valley of the Shadows" (Origin Unknown, Chase and Status remix) is already imported**: source FLAC in
  `rw-audio-work\ToAddTry4`, built pack in `rw-audio-work\packs\origin_unknown_valley_of_the_shadows_chase_status_remix`,
  track and transition JSON in `content/music/`. The pack format has a separate bass stem
  (`src/audio/stem_transport.gd` fixes the stem keys kick, snare, bass, other), so the bass lock can be real,
  not a volume trick. To be confirmed on the pack's files in the first gameplay step.
- The minigame system (`src/minigames/minigame_activity.gd`, `minigame_controller.gd`,
  `src/run/run_minigame_host.gd`) assumes rhythm continues: `engine.hold` is set while an activity lives and
  block results still count and can interrupt it. An explicit activity *mode* is needed, as the brief says.
- The map format (`src/story/world/story_map.gd`): sectors with polygon, floor, ceiling, textures, light,
  fog; walls; "things" that are billboards or lights; waypoints, spots, silhouettes, occluders. No portals,
  no height steps rendered as drops or bridges, no decal kind beyond the A6 wall cards. The renderer needs
  extending for ledges, bridges over voids, the Mothership ring and the Underworld cliffs.
- The rail (`src/run/run_rail.gd`) is a stepped state machine over waypoints: moves are `player_move`
  actions scheduled at song time for a number of bars, driven by block results from `RunPlay`. Continuous
  journeys through doors and around corners need polyline routes between waypoints, still scheduled by the
  same clock.
- Save: `user://story_run.json`, `VERSION 2` in `src/run/run_progress.gd`; the bedsit and rave state go in
  as version 3 with defaults.
- `AGENTS.md` does not exist (the briefs say "wherever applicable"); `docs/PICKUP.md`, `HANDOVER.md`,
  `STORY_25D_PLAN.md`, `CONTINUOUS_RUN.md` do.

## How the run survives stopping

- **One resume file**: `docs/parallel-development/RUN_LOG.md`, on the integration branch, rewritten at every
  checkpoint: the current stage, each stream's branch and last pushed commit, each agent's package and
  state (running, checkpointed, sent back, merged), and the next action for the lead. A fresh session reads
  it, fetches, and resumes. The lead keeps it current; it is the first thing pushed and the last.
- **Checkpoint rhythm**: every agent works in its own worktree on a `wip/` branch and commits a `WIP:`
  checkpoint at least every hour and after every passing filter; the lead pushes `wip/` branches at each
  checkpoint and the integration branches after every verified merge. No work is left uncommitted
  overnight. Before any push: no audio from the 61 recordings, no WAD, no Doom textures.
- **Pause points** at the end of every stage: everything merged, suites green, pushed, `RUN_LOG.md`
  says "pause point N reached". The PC can be switched off there without losing a step. Inside a stage the
  worst case is losing the last hour of one agent's work.
- **Cut-offs**: when the limit bites mid-stage, agents are told to checkpoint and stop; their transcripts
  stay and they are resumed by message, not restarted. At most four agents run at once.
- **Scripts over hands**: anything run twice gets a script (`tools/doom/`, `tools/story/shoot_*.sh`,
  `tools/dev/*.cmd`), so a restarted session repeats a check in one line.

## Who does what (models)

| Work | Model | Why |
|---|---|---|
| Planning, contracts, rulings, merges, reviews of shots, final judgement | Fable (the lead) | the only one holding the whole picture |
| Shared engine changes: renderer extension (height steps, drops, bridges, portals), continuous rail paths, the activity-mode host, the bass lock in the stem transport, race renderer support | Opus | hard engine work on shared files; one owner each |
| Visual polish passes against the references (two rounds per scene), the independent review of each stream | Opus | the owner asked for polish with Opus; judgement of images |
| Geometry conversion tools, scene data, hotspot tables, rail journeys, activity logic (cloakroom, bar), race simulation, bedsit data, tests, docs, manifests | Sonnet | repeatable, well-specified, cheap |
| Surveys, file listings, counting, shot sheets, log reading | Sonnet (Explore) or Haiku | read-only, cheap |

## Stages, times and pause points

Times are wall-clock with up to four agents in parallel. "Day" is one working day of sessions; the weekly
usage limit decides how many days fit in a week (last week, about two heavy days used the week), so the
honest unit is **three usage-weeks** for everything below, four if the limit bites hard or the WAD arrives
late and scenes are redone on real geometry.

### Stage A: finish and merge the in-flight work, then `main` (2 days)

Exactly `TO_MAIN_PLAN.md` phases 0 to 4: checkpoint the cut-off work, resume the seven agents, merge the
eight branches, the shared wiring (hub links, ways back, pinned tests, the wall test), the Warehouse hub
entrances, housekeeping (40 merged branches, 8 stale worktrees, docs, rulings), the final checks, the owner's
play and listen, `main` on the owner's word, fresh branches.

**Pause point A**: `feature/one-pc` final, green, pushed; `main` moved or waiting only on the owner.

Stage B can start on day 2 while the owner plays, since it branches from the final `feature/one-pc` head.

### Stage B: contracts and the two pilots (3 days)

B1, contracts first (lead + one Opus, half a day): `docs/parallel-development/CONTRACTS.md` and fixtures
on `feature/shared-contracts`:

- scene entry/exit (a scene id, a theme, an arrival pose; exit by route or by "home");
- theme selection (bedsit facing to rave theme, data);
- rail destinations and arrival poses (polyline routes between named spots, bars per leg, the stable
  choice viewpoint);
- activity entry/results/exit (`ActivityMode`: `rhythm` as today, `replace` for cloakroom and bar,
  `overlay` for racing) with the table from the brief: pads, world input, penalties;
- input ownership (one owner per tap: pads, world choices, activity controls; never two);
- puzzle progression (per-rave flags: bass, cloakroom, bar; race results; bedsit facing; save v3);
- bass unlocking (a lock on the bass stem in `stem_transport.gd`, separate from mix volume, unlocked at
  a boundary at the current transport position);
- race rendering and camera poses (a road course as StoryMap sectors, vehicle things, cockpit layer).

B2, environment pilot (Opus engine owner + two Sonnet agents, 2.5 days):

- `art/reference/doom_worlds/` with the 16 PNGs copied unchanged and `manifest.json` (scene, Doom map,
  primary and secondary image, implementation files);
- `tools/doom/`: a WAD reader (vertices, linedefs, sidedefs, sectors; coordinate and scale conversion,
  winding, sector adjacency, heights) and, because there is no WAD today, a render-tracing path (the
  ian-albert PNG traced into the same intermediate form by hand-placed vertices in a JSON, with every
  uncertain edge flagged); convex decomposition into the StoryMap sector format with no cracks and the
  same connectivity; a check script (valid sectors, heights, portals, traversable waypoints);
- the renderer extension (Opus): floor steps and drops, bridges over voids, ledges with a railing, the
  far side of a void drawn, portals/occlusion for the rooms behind; mobile budget kept (measured on the
  Warehouse and the Mothership heavy views, desktop figures, phone figures separate);
- continuous rail paths (Opus): `player_move` over a polyline, gentle turns, eye height from the floor,
  the stable choice viewpoint, pause/restart/tempo unchanged;
- the Warehouse (MAP07) end to end: geography, arrival, reference viewpoint, default stay, three guide
  characters with idle/available/selected/committed states (no rings), routes to the three destinations
  (as world transitions at a believable threshold), shots at desktop and 20:9, a movement recording.

B3, gameplay pilot (Opus host owner + two Sonnet agents, 2.5 days, in parallel with B2):

- the bedsit: one room, four facings, turning wraps, bottom stays, forward leaves for the facing's rave;
  no rhythm failure forcing departure; dev compass overlay; fixed theme mapping (N Space, S Magic, E
  Dinosaurs, W Transport); the four world regions separate from the pads;
- the activity-mode host (Opus, shared file): `replace` suspends judging, energy loss, wobble, falls,
  forced routes and rail progression; restores on a clean boundary with a lead-in; no phantom misses;
- the bass lock (Opus): the stem lock in the transport, the DJ-deck interaction on the stage, the audible
  and visual change, persistence for the visit;
- one rave (Space, on the Mothership's geography from B2 when it lands, a shell before that) with the
  stage route and the bass puzzle playable end to end; the legacy opening kept behind the flag.

**Pause point B**: both pilots play in the running game, their shots reviewed by the lead, both feature
branches pushed, `CONTRACTS.md` final enough that the breadth work needs no engine changes it does not
already name.

### Stage C: breadth (5 days)

Environment stream (three Sonnet scene agents at a time, the Opus engine owner on call, lead reviews):

- the remaining seven scenes in two waves on the pilot's pipeline: wave 1 Bar (MAP02), Booth (MAP04),
  Chill-out (MAP08); wave 2 Balcony (MAP15), Dock (MAP13), Mothership (MAP11), Underworld (MAP29). Each:
  traced geography (approximate, flagged), curated rail journey, the reference viewpoint, three guides,
  default stay, several reveal viewpoints, recovery moves, shots and a recording, a view test over every
  choice viewpoint (targets visible, not behind walls, not overlapping, not on the pads);
- the eight-scene routing as a second narrative graph behind the flag, an audit of its differences from
  the main graph written down, world transitions at thresholds;
- `tools/doom/check_world.py` and tests for conversion and rail traversal.

Gameplay stream (two Sonnet agents + the Opus host owner):

- the cloakroom (same/different over four symbols, SAME left and DIFFERENT right, a reference symbol,
  scoring against the previous symbol after wrong answers too, balanced sequences, fast and slow coat
  processing, one score per trial, eight coats, leave and return safe);
- the bar (pictorial order, demonstrated then hidden sequence, four ingredient buttons, two then three
  ingredients, remake on error, four drinks; per-theme ingredients from data);
- street racing: a deterministic race model (distance, speed, rivals, decisions, rhythm, collisions,
  recovery, finish order; minimum speed; 60 to 90 s course), timed situations with a reachable safe
  response and a visible countdown that freezes on pause, four driving regions separate from the pads,
  smooth lane changes; the road course on the StoryMap renderer with the engine owner's support;
- the other three raves (Magic on the Chill-out lounge geography, Dinosaurs on the Underworld, Transport
  on the Dock, each with its own silhouette and circulation, themed props, customers and guides from data),
  the race entrance and the way home in each;
- save v3 with migration defaults; per-rave completion visible in the world.

**Pause point C**: all eight scenes and all four raves exist and play; every activity and the race work in
at least one rave; both streams merged from `feature/shared-contracts` with no conflicts outstanding;
pushed.

### Stage D: polish, verification, integration (3 days)

- **Visual polish, Opus, two rounds**: every scene's in-game captures beside its reference image; geometry,
  framing, materials, lighting corrected on the observed differences; the style guide's texel density and
  the daylight/night exposure rules; 20:9 frames; the guides' costumes and silhouettes checked against the
  paintings; then a second round on the lead's notes. The four raves get the same treatment against the
  theme brief (the concept images as material references).
- The independent review (Opus, fresh context): each stream's branch read against its brief, a list of
  gaps, not fixes.
- Verification: the full suite on each feature branch; the conversion and rail tests; the activity tests
  from the brief (four turns return, each facing's rave, bottom keeps facing, bass locked until repaired
  and in sync after, cloakroom correct after wrong answers, bar retries, no phantom failures, ownership
  restored, racing keeps both inputs, pause freezes deadlines, both skills move the result, every race
  finishes, returning preserves rave state); walks; performance on the heavy views (desktop figures named
  as such).
- The owner plays both: `tools\dev\play_doom_worlds.cmd` (whole set and `--scene <id>`) and
  `tools\dev\play_bedsit.cmd`; fixes on the branches.
- Draft PRs for both feature branches with the comparison links; not merged.
- `HANDOVER.md`: what was implemented, inspected, tested, measured, and what is missing (the WAD, the
  phone, anything not run).

**Pause point D**: both branches final, green, pushed, PRs drafted, handover written.

### Stage E: the APK (1 day)

The Android export with the 61 tracks bundled (the re-encoded packs inside the APK, never in Git), the
legacy campaign and both new branches' content if the owner wants them in one build, or `main` alone;
phone measurements if a phone is plugged in, otherwise written down as not done.

## Branches

| Branch | From | Holds | Merged by |
|---|---|---|---|
| `feature/one-pc` | `origin/main` | everything in stage A | the lead, into `main` on the owner's word |
| `feature/shared-contracts` | `feature/one-pc` final | contracts, fixtures, the shared engine changes (one owner each) | the lead; both feature branches merge *from* it |
| `feature/doom-layout-worlds` | `feature/shared-contracts` | the environment stream | the lead merges `wip/env-*` into it; never into `one-pc` or `main` without instruction |
| `feature/bedsit-raves` | `feature/shared-contracts` | the gameplay stream | the lead merges `wip/play-*` into it; same rule |
| `wip/env-<scene>`, `wip/env-tools`, `wip/engine-<topic>`, `wip/play-<activity>`, `wip/polish-<scene>` | the stream branch | one agent's package each, checkpointed and pushed | the lead, `--no-ff`, after the filtered tests |

Ownership of shared files (one writer at a time): `run_play.gd`, `run_minigame_host.gd`, the judge, the
stem transport and transition director, `story_world.gd`, `story_map.gd`, `run_rail.gd`,
`make_scenes.py`, `run_progress.gd`. Everyone else works against the contracts and fixtures.

## Decisions the owner is asked for before the start

1. **The WAD.** Do you own Doom II (Steam or GOG)? If so, copy `doom2.wad` to
   `C:\Users\joesa\rw-audio-work\doom\doom2.wad` (outside Git) and the geography is real. If not, it is
   traced from the public map renders and labelled approximate everywhere; it can be swapped later.
2. **The shape of the game.** My reading of the two briefs together: the bedsit becomes the game's
   opening; the four raves are its first act; the eight Doom scenes are a separate explorable set behind a
   flag (and the raves borrow four of their geographies: Space on the Mothership, Magic on the Chill-out
   lounge, Dinosaurs on the Underworld, Transport on the Dock); the existing five-location campaign stays
   playable from a legacy entry. Is that right, and are those four borrowings the ones you want?
3. **Order.** Stage A first (finish and merge what is in flight, `main` on your word), with stage B
   starting on its second day while you play. Or stage B at once, with stage A's merges alongside; I
   recommend A first, because stage B branches from A's final head and merges get expensive otherwise.
4. **The track.** The copy on the PC is the Chase and Status remix of "Valley of the Shadows"; it is the
   one the opening rave uses unless you have the original.
5. **The push policy** stays as it is: integration branches after every verified merge, `wip/` branches at
   checkpoints, nothing to `main` until you say, no force-pushes, no audio or Doom data in Git.

## Risks

- **Scope**: twelve environments, four activities, a race and a renderer extension. The stages are ordered
  so a stop after any pause point leaves a complete, playable, pushed piece; polish is last on purpose.
- **The usage limit**: three usage-weeks is the honest figure; the resume file and the checkpoint rhythm are
  built for the cut-offs.
- **Approximate geography** until a WAD appears; the brief allows it if it is called what it is.
- **The renderer**: drops, bridges and the void are the first real 3D the 2.5D renderer has to fake;
  the Warehouse and Mothership pilots exist to find out early whether the mobile budget holds.
- **Audio**: WASAPI stopped opening on this PC last week; the bass-lock listening check needs it back.
- **No phone yet**; everything is desktop and headless until stage E.
