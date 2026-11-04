# The continuous story run

The game is one run through the five 2.5D worlds. The home screen has **Play** (the run), **Story chapters** (the finished chapter campaign, its own menu and saves,
`story_campaign.tscn`), **Start from a reached level** and **Settings**; the military campaign, loadout and duel are developer-only. Branch `feature/continuous-story-run`, built on the verified merge of `feature/story-25d` and the
Warehouse music test (see "Baseline" below).

```
godot --path .                                    # home: Play / Story chapters / Start from a reached level / Settings
godot --path . res://src/run/run_play.tscn        # straight into the run (RW_RUN_START=<level id> starts on a level)
```

## The phase

174 BPM, 4/4. A phase is 64 beats (22.07 s) of one level, four blocks of 16 beats. One required cue family is active at a time.

| Beats | Stage | Mix (drums / bass / synth) | Cues |
| --- | --- | --- | --- |
| 1-16 | Drums alone | 1.0 / 0 / 0 | drums |
| 17-32 | Bass enters | 0.5 / 1.0 / 0.45 | bass |
| 33-48 | Drums return | 1.0 / 0.5 / 0.45 | drums |
| 49-64 | Bass strongest | 0.4 / 1.0 / 0.6 | bass, plus the direction choice |

* **Advance or hold.** Each block is judged at its decision beat (12.75 of 16, once its last cue and hit window have resolved). A pass moves the stage one
  step on; a miss holds the stage (and so the cue family) for another block. Missing block 1 and passing block 2 reveals the bass on beat 33. The phase is still
  exactly 64 beats, the choice window is always the last block, and the next phase starts on drums alone.
* **Reveal.** Bass and Synth start together from the beginning of their phrase at the reveal block and then keep running while the foreground changes. Bass cues
  come from the bass phrase position (reveal beat = phrase beat 0); drum cues from the drum phrase position (phase downbeat = phrase beat 0).
* **Cue-free guard.** Cues occupy beats 0-12 of a block (a hold is cut to end by beat 12); the last four beats are empty so hit windows and hold tails resolve
  before the focus switches and the next block's cues, charted at the decision beat, are already falling in.
* **Smooth gains.** Mix changes ramp over 0.35 s, scheduled on the clock at the block boundary.
* **Choice window (beats 49-64).** At least two arrows (real buttons, clear of the pads, 100+ px targets) from the first beat of block 4 even if the build stalled. Tap or press
  Left/Right/Up to choose; change your mind until the phase ends; the marked `[DEFAULT]` route is taken when nothing is chosen. The destination and its sound treatment
  commit on the next downbeat. The effect for the window is a **riser** when the last bass stage is already reached at beat 49, a **fall** otherwise
  (`assets/run/riser.wav`, `fall.wav`, 16 beats each, synthesised by `tools/content/make_run_effects.py`).
* **Survival.** Crowd energy is the survival meter (start 60). A pass adds 5-11, a fail takes 3-10 (more the further under the pass line). At zero the run ends on the
  next block boundary with a 2-beat fade; six blocks at zero credit in a row are needed from a fresh start, so a rough block is recoverable. The last block counts.

All numbers are in `content/run/run.json` (`timing`, `judgement`, `energy`, `stages`, `mix`, `effects`): thresholds and gains are tunable without code.

## Route map

Depth is the progression point; difficulty tier = min(depth, 4). Every level offers at least two arrows. Levels at one depth **share one chart** (identical required cue
events whichever way you came) and the same difficulty tier; they differ in place, treatment and, where an alternate render exists, in sound.

| Depth | Level | World | First arrow (default) | Second arrow |
| --- | --- | --- | --- | --- |
| 1 | Warehouse | Night One | up: The Mothership | right: The Underworld |
| 2 | The Mothership | Mothership | left: The Hospital | right: The Ward |
| 2 | The Underworld | Underworld | left: The Hospital | right: The Ward |
| 3 | The Hospital | Hospital | left: Hospital, late | right: Ward, late |
| 3 | The Ward | Ward (Mental hospital) | left: Hospital, late | right: Ward, late |
| 4 | The Hospital, late | Hospital | left: itself (loops) | right: Ward, late |
| 4 | The Ward, late | Ward | right: itself (loops) | left: Hospital, late |

Depth 4 is the last tier, so strong play can go on forever through the two late worlds. Every level can be reached from the start (`RunData` warns otherwise).

## Difficulty

`beatshaper.py` writes four tiers per pack. A tier keeps cues with their source timing and thins the rest: whole beats first, then half beats, then the rest, with a
minimum gap per tier (drums 1, 0.75, 0.5, 0.5 beats; bass 2, 1.5, 1, 0.75 beats) and holds shortened to end before the next cue. Higher tiers therefore add density and
syncopation; bass holds are always holds. At the same depth every sibling plays the same tier of the same chart pack.

## Music assignment

`content/story/music.json`: per level `audio` (the pack whose recordings play), `chart` (the pack whose cues are charted), `treatment` (filter, distortion, reverb on that
phase's own drum and bass buses, `content/run/run.json` `treatments`) and `temporary`. Today: Warehouse = Lv1 Warehouse; Mothership = Lv2 Alien Spaceship; Underworld = the same
recordings with the `underworld` treatment (temporary); Hospital and Ward = Lv1 Warehouse (1) with their own treatments (temporary); the late levels = Lv2 Alien Spaceship (2)
(temporary). Importing and assigning new sets is `docs/MUSIC_IMPORT.md`; the per-level shopping list is `docs/MUSIC_HANDOFF.md`.

## Saves and migration

`user://story_run.json` records every level as *reached* the moment a phase starts on it. Home shows **Start from a reached level** (locked cards say how a level opens),
a restart from a level gives its authored opening (drums alone, fresh energy 60), and a loss offers **Retry this level**, **Choose a reached level** and **Home**.
The old chapter save `user://story_campaign.json` is never modified or deleted: the first time the new save is created it is read once and every chapter that had been
played becomes a reached level (Night One -> Warehouse, Mothership, Underworld, Hospital, Mental hospital -> Ward), with a one-line note on the home screen.

## How it is built

| Piece | File | Role |
| --- | --- | --- |
| Data | `src/run/run_data.gd`, `content/run/run.json`, `content/story/music.json`, `songs/packs/*` | merged, validated node table |
| Logic | `src/run/run_engine.gd` | pure: song time in, events out (cues, mix, reveal, route window, commit, depletion); drives `PadJudge` |
| Audio | `src/run/run_audio.gd` | silent 64-beat loop is the clock (one unbroken beat grid); per-phase voices started on it with lateness compensation; riser/fall; treatments |
| Scene | `src/run/run_play.gd`, `run_hud.gd`, `run_over.*`, `run_levels.*` | hosts it all; reuses `StoryStage`, `StoryPadView`, `StoryNoteLane`, `StoryDeck`, `LaneInput`, `SongClock` |
| Save | `src/run/run_progress.gd` | reached levels, migration |
| Import | `tools/content/beatshaper.py` | scan, check, import, assign, apply, validate |

World swap: the stage of each world is built once and kept; candidates for the next level are built during cue-free guards (one per guard) and the swap on the downbeat is a
visibility change plus a flash. Audio for the candidates is loaded on a thread when the route window opens. The old chapter scenes (`story_play`, `story_campaign`, `story_result`,
`story_interlude`) and the military screens still exist in the repository for the art pipeline, tests and the developer button (editor only), but nothing in the run path
or the home screen reaches them; the run path does not read the loadout, the library, the campaign rules or `Match`.

## Verification

Baseline: see the top of this file's branch history. On the merged `main` the Warehouse recording check (real scene, scripted perfect play) showed all three loops explained
99.6-100 %, the same delay in every lap (spread 0.00 ms over 15 laps) and drum transients +2 ms from the cues.

Automated (headless GDScript, `tests/test_run_engine.gd`, `test_run_progress.gd`, `test_run_scene.gd`; Python `tools/content/test_beatshaper.py`):
the four-step mix, a held and a delayed reveal, the 64-beat phase and reset, riser versus fall, default and changed routes, identical required cues for sibling routes,
difficulty rising with depth, failure ending on a block boundary with a fade, a recoverable rough patch, save/migration/corruption, route data validation, touch targets
clear of the pads and on screen in an 844x390 landscape view, a tap choosing a route, the chosen level entering on the exact downbeat and being saved as reached, the world swap.

Recorded (real scene, real `RunAudio`, dummy audio driver, Music bus captured; `tools/story/record_music.gd` + `check_run_audio.py`): per block the recording is fitted as
drums + bass + synth + riser/fall and the fitted gains compared with the stage's: all within 0.03 of the table on untreated levels, 99-100 % of the signal explained;
a delayed reveal starts bass and synth from beat 32; the riser and fall are present at -6 dB; bass and synth sit within 3 ms of the drums, the effect within 6 ms; the same
delay (within 6 ms, one mix chunk) from phase to phase and across a world change; after a 4 s pause in the middle of a phase the audio is back on the grid within 0.4 ms and the
voices are 0.0 ms apart.

Seen (virtual clock, real window, screenshots in `docs/shots/run/`): all seven levels in all five worlds, the route window with the default marked, a world swap, the phone-sized view.

Not done: nothing here was listened to or played by hand on a phone; the dummy audio driver has no output latency, so real-device latency is covered only by the existing calibration setting;
the treated levels (Underworld, Hospital, Ward, the late levels) were checked for timing but their treatment settings were not judged by ear; the riser and fall are synthesised and have not
been auditioned. See `docs/MUSIC_HANDOFF.md` for what is temporary.

## The run on the polished 2.5D worlds (WP-A1, 2026-11-04)

Verified on `feature/run-on-25d` (the run, the Deathtrap Dungeon and the 2.5D polish merged):

* `--import` clean; the full Godot suite 41,143 checks, 0 failures (the Python `mido` failures of the content build tests are the known, unrelated ones); the 26 trial tests pass.
* Chapter walk-through (`tools/story/walk_campaign.sh`, all five paths: perfect, none, sloppy2, mixed_a, mixed_b): `walk-through: OK`, every chain, ending, menu unlock and save as expected.
* Run recording (`tools/story/record_music.gd` on `run_play.tscn` with perfect play and the routes up,left,left,right,left, then `tools/story/check_run_audio.py`), 100 s, 5 phases.
  **Found:** the first recording after the merge failed its mix fit on the Warehouse (the synth fitted 0.09 against 0.45 in blocks 2 to 4, 94 to 97 % explained, delay spread 15 ms).
  **Cause:** the 2.5D polish made a world's stage expensive to build: every world's people pages (16 pages of 2048 px) were decoded from the imported textures on the main
  thread, so building one stage took 0.84 to 2.35 s (`tools/run/profile_build.tscn`: people sheets 0.6 to 1.6 s of it). The run builds the next candidate world in a cue-free guard
  (1.4 s), so the stall swallowed the guard and delayed `RunAudio`'s gain changes at the block boundary.
  **Fix:** `StoryPeople.prewarm()` decodes a world's pages on a worker thread when a level starts (the candidates are the worlds its routes lead to), and the stage build only uploads them:
  builds now take 0.53 to 0.77 s (data 5 ms, people/crowd setup 270 to 550 ms, world 205 to 460 ms) and start at beat 12.6 of a block instead of 13.2. Re-recorded: every block of the
  Warehouse and the Mothership within 0.01 of the table's gains, 99.7 to 100 % explained, bass and synth within 3 ms of the drums, the riser within 6 ms, "RESULT CHECK" as before.
  The per-phase delay still drifts by 15 to 25 ms over four phases here (the first run measured spread 0.00 ms on an idle machine); both recordings were made while other jobs were loading the
  machine, so that number needs re-measuring on an idle one.
* The 360-line default, the settings (pad size, motion, reduced effects, contrast) and the activities all pass through unchanged: `_build_stage` applies `Session.story_lines`, `reduced`,
  `high_contrast` and `effective_story_motion` to every stage, and the crowd's activity picks read the band of `engine.energy` (tests/test_run_rail.gd, test_run_matrix.gd).

## Rails and activities in the run (WP-A3)

The run reuses the chapters' rail camera but not their director: the run owns the stage, `RunJourney` (pure) turns the engine's events into stage actions and `run_play.gd` hands
them to the active world's `StoryStage`. Each node in `content/run/run.json` has a `rail`:

```
"rail": {"good": [{"to": "steps", "role": "dancer", "style": "walk", "bars": 3}, ...],   "bad": [{"to": "floor_edge", "role": "queasy", ...}, ...],
         "arrive": "door", "glances": [{"by": -28, "bars": 2}, ...], "strolls": [{"fwd": 1.6, "bars": 3}, ...], "exits": {"up": "door", "right": "tunnel"}}
```

| Node | Good rail (up from home) | Bad rail (down) |
| --- | --- | --- |
| Warehouse (floor_centre) | steps, stage, balcony, booth | floor_edge, corridor, cubicle |
| Mothership (deck_centre) | gallery_in, reactor_in, bridge_in, helm | gallery_in, medbay, exam |
| Underworld (arena_floor) | court_in, throne, pit_stage | furnace_chains, cage |
| Hospital (bed) | corridor_in, cafe_in, bandstand | ward_chair, quiet, bed |
| Ward (day_centre) | corridor_in, art_in, stage | treat, quiet |
| Hospital, late (garden_edge) | bandstand | garden_in, quiet |
| Ward, late (stage_edge) | stage | court_in, treat |

* **Steps.** At each block decision (beat 12.5, inside the cue-free guard) a pass steps one place up the good rail and stays at the top; a hold steps one place along the bad rail (from
  the good rail it drops to the first bad place). Two holds in a row start the queasy look (`fx_queasy`, stronger with more holds), reaching the bottom plays `sick_beat` once, and a pass
  from the bad rail walks back one place toward the floor (role `recovered`, the look clears, `dancer` again at home). `player_role` follows the place (dancer, on_stage, dj, queasy, sick,
  recovered). A loop ("round again") keeps the rail state; a new level starts it again from home.
* **Moves** are `player_move` of 2 to 4 bars that start on the decision beat; `RunRail.pick_bars` shortens one (never below 2 bars) when the chart would make more than half its bars dense
  (more than one note per beat), the rule of the chapter director's dense-run warning, which is therefore silent (asserted over the whole policy matrix).
* **Every block** has a glance (`player_look by/pitch`, varied through the node's list) and most blocks an in-room walk (`player_walk`, skipped while a journey move is under way).
* **Route window.** The touch arrows stay (phones need them) and, while the window is open, the room's exits are lit (`RunExitsView`): a pulsing doorway at the waypoint of each candidate route,
  projected with the stage's own camera, or an arrow at the screen edge on the side it lies when it is out of sight; the chosen one is gold.
* **World swap** (`RunPassage`, `RunPassageView`): when the selected route at beat 62 leads to another world the frame closes to a lit doorway over the last two beats, the swap happens on the
  downbeat exactly as before (audio untouched), and the new world's camera starts at its doorway (`arrive`, a cut hidden by the closed frame), walks to the start waypoint from beat 62 (the walk
  starts in the guard) while the frame opens over 2.5 beats. Same-world routes and loops do not close the frame. Everything is a function of song time.
* **Activities** need nothing new: the stage already reads `engine.energy` each frame and the crowd picks each person's activity from the sector's list for the energy band.
* The fourth step of a phase (decided at beat 60.5) is mostly cut by the swap 3.5 beats later, so the top of a four-place rail (the booth) shows for a moment only in a loop; the logical step
  still counts (the matrix records it).

### Route lock (the chart of the next phase)

Block 0 of the next phase is charted at the last block's decision (beat 60.5), before the player's choice is final, and levels may chart different packs. `RunEngine` therefore charts it from
the **selected** route at that moment (the default, or the player's pick) and **locks the chart**: until the downbeat `choose()` refuses a route whose chart pack differs from the one already
charted (a route with the same pack may still be chosen), and the route buttons of such routes grey out. The window opens at beat 48 and the lock falls at beat 60.5, so there are 12.5 beats to change
one's mind freely. (tests/test_run_engine.gd)

### Playtests

* `tests/test_run_matrix.gd`: perfect, accuracy 0.9 / 0.8 / 0.7 / 0.5, sloppy (0.8 with 110 ms jitter) and none, seeds 1 to 3 (seed 1 default routes, 2 the second arrow, 3 random), up to 8 phases. Asserts
  survival or depletion, depth, the rail kinds visited, a glance in every block, no move outside a guard or outside 2 to 4 bars or on dense cues, and the camera in a valid sector of the map on
  every world's real `StoryPlayer` (sampled every 0.25 s). Result: perfect, 0.9, 0.8, 0.7 and sloppy survive all 8 phases and reach depth 4 (perfect never leaves the good rail; 0.8 and 0.7 visit the
  bad rail 4 to 12 times and win back); 0.5 ends in 4 and 7 phases (seeds 1, 2) or survives with 45 energy (seed 3), always reaching the sick beat; none ends in phase 2 on every seed, at the sick beat.
  The run is forgiving for skilled players (0.7 survives): tuning belongs to WP-C4.
* `tools/run/walk_run.sh`: the real scenes on the virtual clock, an isolated save, five scripted paths that together visit all seven levels (perfect_a: warehouse > mothership > hospital > ward_late >
  hospital_late; perfect_b: warehouse > underworld > ward > hospital_late; sloppy; none; a start on ward_late) and check the level sequence, rail places, glances, the run save and that no chapter save is
  written. Result: `run walk-through: OK`.
* `tools/run/capture.sh`: screenshots in `docs/shots/run`: `node_*` and `route_*` per level, `rail_<node>_<place>` per rail place, `journey_*` (the camera really walking), `passage_*`, phone, wide, reduced
  motion, 180 lines, and the home screen with both entry points pressed by key (`home_*`).
* `tools/run/frames.sh` and `tools/run/profile_build.tscn`: frame times and stage-build times per world (numbers below).

### Frame numbers per world (`tools/run/frames.sh`, 2026-11-04)

Real-time, 1280x720, vsync off, dummy audio, perfect play, two phases per start level, on the reference laptop (Intel HD 520) **while other jobs shared the machine**, so read them as an upper bound
(the chapters' idle budget is 12 ms mean, 20 ms p95):

| Start level | Frames | Mean | p95 | Max | Over 50 ms |
| --- | --- | --- | --- | --- | --- |
| Warehouse | 2702 | 16.5 ms | 22.0 | 592 | 6 |
| Mothership | 2609 | 17.2 ms | 21.9 | 550 | 2 |
| Underworld | 2459 | 18.4 ms | 23.5 | 547 | 3 |
| Hospital | 2659 | 17.0 ms | 20.8 | 598 | 1 |
| Ward | 2601 | 17.4 ms | 22.1 | 563 | 1 |

The over-50 ms frames are the stage builds of the candidate worlds (0.48 to 0.66 s each now, was 0.8 to 2.4 s: people/crowd setup 250 to 270 ms, the 3D world 140 to 290 ms), each done once in a
cue-free guard from beat 12.6; the first stage of a run builds before the countdown (0.66 to 1.5 s). Further splitting a build across guards would remove them; not done.
