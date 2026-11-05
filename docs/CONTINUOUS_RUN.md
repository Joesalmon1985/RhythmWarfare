# The continuous story run

The game is one run through the five 2.5D worlds, as seven **worlds** (the five maps, the Hospital and the Ward twice: once on the way in, once "late"), each a small graph of **scenes**.
A scene is one 64-beat phase at a place in a world (a room: the floor, the bar, the booth ...). The player walks a path of three to five rooms (66 to 110 s) before the world exit sends them on. The home screen has **Play** (the run), **Story chapters** (the finished chapter campaign, its own menu and saves,
`story_campaign.tscn`), **Start from a reached level** and **Settings**; the military campaign, loadout and duel are developer-only. Branch `feature/continuous-story-run`, built on the verified merge of `feature/story-25d` and the
Warehouse music test (see "Baseline" below).

```
godot --path .                                    # home: Play / Story chapters / Start from a reached level / Settings
godot --path . res://src/run/run_play.tscn        # straight into the run (RW_RUN_START=<level id> starts on a level)
```

## The phase

174 BPM, 4/4. A phase is 64 beats (22.07 s) of one level, four blocks of 16 beats. One required cue family is active at a time. (A scene of a PATH may play several phases in a row, its LAPS: the main run never
does, see "Two laps per path scene" at the end.)

| Beats | Stage | Mix (drums / bass / synth) | Cues |
| --- | --- | --- | --- |
| 1-16 | Drums alone | 1.0 / 0 / 0 | drums |
| 17-32 | Bass enters | 0.5 / 1.0 / 0.45 | bass |
| 33-48 | Drums return | 1.0 / 0.85 / 0.45 (bass 0.5 before the audio polish) | drums |
| 49-64 | Bass strongest | 0.4 / 1.0 / 0.5 (synth 0.6 before the audio polish) | bass, plus the direction choice |

The audio polish (docs/HANDOVER.md A10) added `mix.recipe_bass_floor`, `mix.carry_bass` (the bass of the previous scene under the drums-alone block, same music family only), the bass bus (`mix.bass_bus`, per path and per scene) and the run level (`mix.gain_db`); `tools/run/measure_mix.py` measures it all.

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

## Worlds, scenes and the route map (WP-A5)

`content/run/run.json` has `worlds` (id, title, `map` = the art world the stage is built from, `depth`, blurb) and `nodes`, which are the **scenes**:
`{id, world, scene, title (the room), entry, exit_scene, next: [{to, dir, label, loop?}], place: {waypoint (home), rail: {good, bad, arrive, glances, strolls, exits}}}`. `place` is the
run agent's rail format (WP-A3) for the room: `rail.good`/`bad` are places within reach of the room, `rail.arrive` the doorway the camera comes in by from the previous scene, and
`rail.exits` the doorway of each route (`dir` -> waypoint) that is lit while the route window is open. Rules (`RunData`, tested in `tests/test_run_progress.gd`): one `entry` scene per world
and its id is the world's id (the save's `reached` ids never change), one `exit_scene`, every scene reaches the exit over routes that stay in the world, the world graph is acyclic
except through a route marked `loop`, only the exit scene leads to other worlds (to their entry scenes, one depth deeper, or the same depth at the last tier), every route has a lit
doorway in `rail.exits`, and every home, rail place, arrival and doorway exists in the scene's map. `tools/run/make_scenes.py` authors the data (scenes, the 100 doorway and place
waypoints it adds to the five maps, and `music.json`); edit its tables and run it again.

Depth (the difficulty tier = min(depth, 4)) is per world. A path through a world is 3 to 5 phases of 22.07 s:

| World | Depth | Scenes on a path | Duration |
| --- | --- | --- | --- |
| Warehouse | 1 | floor > bar or balcony > chill-out or booth > door | 4 phases, 88 s |
| The Mothership | 2 | deck > gallery or reactor > bridge > airlock | 4 phases, 88 s |
| The Underworld | 2 | arena > court or furnace > pit > throne | 4 phases, 88 s |
| The Hospital | 3 | ward > corridor > day room or cafeteria > garden > bandstand | 5 phases, 110 s |
| The Ward | 3 | day room > art room or dormitory > corridor > courtyard > stage | 5 phases, 110 s |
| The Hospital, late | 4 | garden > cafeteria or quiet room > bandstand (round again) | 3 phases, 66 s |
| The Ward, late | 4 | courtyard > treatment room or dormitory > day room (round again) | 3 phases, 66 s |

The first three worlds on any path are 13 to 14 phases (about 5 minutes) before the late worlds, which then loop for as long as the player survives. A scene's route window offers the scene's `next`:
two or three arrows with the first marked `[DEFAULT]`; a scene with one way on (chill-out, booth, gallery, reactor, bridge, day room, cafeteria, garden ...) shows its single arrow so the window
always opens, the lit door in the room is the way. The exit scene offers the other worlds.

**Warehouse** (`warehouse`, depth 1, tier 1, map `night_one`)

| Scene | Room | Role | Arrows (default first) | Music (audio = chart) |
| --- | --- | --- | --- | --- |
| `warehouse` | The Floor | entry | right warehouse.bar, up warehouse.balcony | `lv1_warehouse` (Lv1 Warehouse) |
| `warehouse.bar` | The Bar | middle | right warehouse.chill, left warehouse.booth | `lv1_warehouse_v1` (Lv1 Warehouse (1)) |
| `warehouse.balcony` | The Balcony | middle | right warehouse.chill, left warehouse.booth | `lv1_warehouse_v2` (Lv1 Warehouse (2)) |
| `warehouse.chill` | The Chill-out | middle | up warehouse.exit | `lv1_warehouse_v2` (Lv1 Warehouse (2)) |
| `warehouse.booth` | The Booth | middle | up warehouse.exit | `lv1_warehouse_v1` (Lv1 Warehouse (1)) |
| `warehouse.exit` | The Door | exit | up mothership, right underworld | `lv1_warehouse` (Lv1 Warehouse) |

**The Mothership** (`mothership`, depth 2, tier 2, map `mothership`)

| Scene | Room | Role | Arrows (default first) | Music (audio = chart) |
| --- | --- | --- | --- | --- |
| `mothership` | The Deck | entry | right mothership.gallery, up mothership.reactor | `lv2_alien_spaceship` (Lv2 Alien Spaceship) |
| `mothership.gallery` | The Gallery | middle | up mothership.bridge | `lv2_alien_spaceship_v1` (Lv2 Alien Spaceship (1)) |
| `mothership.reactor` | The Reactor | middle | up mothership.bridge | `lv2_alien_spaceship_v3` (Lv2 Alien Spaceship (3)) |
| `mothership.bridge` | The Bridge | middle | up mothership.exit | `lv2_alien_spaceship_v2` (Lv2 Alien Spaceship (2)) |
| `mothership.exit` | The Airlock | exit | left hospital, right ward | `lv2_alien_spaceship` (Lv2 Alien Spaceship) |

**The Underworld** (`underworld`, depth 2, tier 2, map `underworld`)

| Scene | Room | Role | Arrows (default first) | Music (audio = chart) |
| --- | --- | --- | --- | --- |
| `underworld` | The Arena | entry | right underworld.court, left underworld.furnace | `lv2_alien_spaceship_v2` (Lv2 Alien Spaceship (2)) **temporary** |
| `underworld.court` | The Court | middle | up underworld.pit | `lv2_alien_spaceship_v3` (Lv2 Alien Spaceship (3)) **temporary** |
| `underworld.furnace` | The Furnace | middle | up underworld.pit | `lv2_alien_spaceship_v2` (Lv2 Alien Spaceship (2)) **temporary** |
| `underworld.pit` | The Pit | middle | up underworld.exit | `lv2_alien_spaceship_v3` (Lv2 Alien Spaceship (3)) **temporary** |
| `underworld.exit` | The Throne | exit | left hospital, right ward | `lv2_alien_spaceship_v2` (Lv2 Alien Spaceship (2)) **temporary** |

**The Hospital** (`hospital`, depth 3, tier 3, map `hospital`)

| Scene | Room | Role | Arrows (default first) | Music (audio = chart) |
| --- | --- | --- | --- | --- |
| `hospital` | The Ward | entry | up hospital.corridor | `lv4_hospital` (lv4 Hospital) |
| `hospital.corridor` | The Corridor | middle | left hospital.dayroom, right hospital.cafeteria | `lv4_hospital_v2` (lv4 Hospital (2)) |
| `hospital.dayroom` | The Day Room | middle | up hospital.garden | `lv4_hospital_v3` (lv4 Hospital (3)) |
| `hospital.cafeteria` | The Cafeteria | middle | up hospital.garden | `lv4_hospital_v2` (lv4 Hospital (2)) |
| `hospital.garden` | The Garden | middle | up hospital.exit | `lv4_hospital_v3` (lv4 Hospital (3)) |
| `hospital.exit` | The Bandstand | exit | left hospital_late, right ward_late | `lv4_hospital` (lv4 Hospital) |

**The Ward** (`ward`, depth 3, tier 3, map `mental_hospital`)

| Scene | Room | Role | Arrows (default first) | Music (audio = chart) |
| --- | --- | --- | --- | --- |
| `ward` | The Day Room | entry | right ward.art, up ward.dorm | `lv5_asylum` (Lv5 Asylum) |
| `ward.art` | The Art Room | middle | up ward.corridor | `lv5_asylum_v1` (Lv5 Asylum (1)) |
| `ward.dorm` | The Dormitory | middle | up ward.corridor | `lv5_asylum_v3` (Lv5 Asylum (3)) |
| `ward.corridor` | The Corridor | middle | up ward.courtyard | `lv5_asylum_v1` (Lv5 Asylum (1)) |
| `ward.courtyard` | The Courtyard | middle | up ward.exit | `lv5_asylum_v3` (Lv5 Asylum (3)) |
| `ward.exit` | The Stage | exit | left hospital_late, right ward_late | `lv5_asylum` (Lv5 Asylum) |

**The Hospital, late** (`hospital_late`, depth 4, tier 4, map `hospital`)

| Scene | Room | Role | Arrows (default first) | Music (audio = chart) |
| --- | --- | --- | --- | --- |
| `hospital_late` | The Garden | entry | left hospital_late.cafe, right hospital_late.quiet | `lv4_hospital_v1` (lv4 Hospital (1)) |
| `hospital_late.cafe` | The Cafeteria | middle | up hospital_late.exit | `lv4_hospital_v3` (lv4 Hospital (3)) |
| `hospital_late.quiet` | The Quiet Room | middle | up hospital_late.exit | `lv4_hospital_v2` (lv4 Hospital (2)) |
| `hospital_late.exit` | The Bandstand | exit | left hospital_late (loop), right ward_late | `lv4_hospital_v1` (lv4 Hospital (1)) |

**The Ward, late** (`ward_late`, depth 4, tier 4, map `mental_hospital`)

| Scene | Room | Role | Arrows (default first) | Music (audio = chart) |
| --- | --- | --- | --- | --- |
| `ward_late` | The Courtyard | entry | left ward_late.treat, right ward_late.dorm | `lv5_asylum_v2` (Lv5 Asylum (2)) |
| `ward_late.treat` | The Treatment Room | middle | up ward_late.exit | `lv5_asylum_v2` (Lv5 Asylum (2)) |
| `ward_late.dorm` | The Dormitory | middle | up ward_late.exit | `lv5_asylum_v3` (Lv5 Asylum (3)) |
| `ward_late.exit` | The Day Room | exit | right ward_late (loop), left hospital_late | `lv5_asylum_v2` (Lv5 Asylum (2)) |


## The door walk and the world swap

* **A path inside a world** (a `next` to a scene of the same world) is a plain door walk: no frame, the same world stage stays, the scene's rail starts at its arrival place. Three beats before
  the downbeat (beat 61, in the cue-free guard) `RunPlay` latches the selected route once per phase and `RunJourney.leave_walk` starts one `player_move` of 2 to 4 bars (`RunRail.leave`, shortened
  where the next block's cues are dense) from wherever the camera is to the new scene's `arrive` waypoint; the map's portal route takes it through the door and it ends a few beats into the new
  phase. The scene itself starts on the downbeat as any phase does (drums alone, cues charted at beat 60.5, audio on the grid), so the walk is the only visible change. A change of mind after
  beat 61 keeps the walk toward the first pick and the new scene then walks in from where the camera is (`RunRail.door_walk`, a move on the downbeat).
* **A world change** (the exit scene to another world's entry scene, including Hospital to Hospital, late, which share a map) keeps the passage frame: it closes to a lit doorway over beats 62 to 64,
  the camera cuts to the new world's `arrive` waypoint behind it and walks to home while the frame opens (WP-A3, `RunPassage`). A `loop` to the entry scene of the same world is a door walk.
* The Bassment: the wizard waits on the Warehouse floor (`warehouse`) and, with the same route, in the chill-out (`warehouse.chill`); `trial_leave` resumes at the Warehouse entry scene
  (`RunEngine.resume("warehouse")`, a fresh rail, no door walk).

## Difficulty

`beatshaper.py` writes four tiers per pack. A tier keeps cues with their source timing and thins the rest: whole beats first, then half beats, then the rest, with a
minimum gap per tier (drums 1, 0.75, 0.5, 0.5 beats; bass 2, 1.5, 1, 0.75 beats) and holds shortened to end before the next cue. Higher tiers therefore add density and
syncopation; bass holds are always holds. At the same depth every sibling plays the same tier of the same chart pack.

## Music assignment

`content/story/music.json`: one entry **per scene**: `audio` (the pack whose recordings play), `chart` (the pack whose cues are charted), `treatment` and `temporary`. The entry scene plays the world's
base set and the later scenes its variants (tables above): Warehouse `lv1_warehouse` with `_v1`/`_v2`; Mothership `lv2_alien_spaceship` with `_v1`/`_v3`/`_v2`; Hospital `lv4_hospital` with `_v2`/`_v3`;
Ward `lv5_asylum` with `_v1`/`_v3`; Hospital, late `_v1` with `_v3`/`_v2`; Ward, late `_v2` with `_v3`. **No variant is an alternate render of its base set**: every variant's cues differ from the
base pack's (compared by tier), so each is its own chart, played at the world's tier. The Underworld plays Lv2 variants (`_v2`, `_v3`) as **temporary** stand-ins until Lv3 Hell has MIDI. Each scene's
phase starts on drums alone, as ever, whichever pack it plays. Importing and assigning new sets is `docs/MUSIC_IMPORT.md` (`beatshaper.py assign --node <scene id>`); the shopping list is `docs/MUSIC_HANDOFF.md`
(regenerated per scene by `tools/content/music_handoff.py`).

**Sibling scenes and the route lock.** Block 0 of the next phase is charted at the last block's decision from the *selected* route, then locked: a route whose scene charts another pack greys out and
`choose()` refuses it. Siblings that chart the same pack are never locked. In the shipped data the lock applies at the Warehouse floor, the bar and balcony (Lv1 variants `_v1`/`_v2`), the deck
(gallery `_v1`, reactor `_v3`), the Underworld arena, the Hospital corridor, the Ward day room, the late entries and every exit scene (`beatshaper.py validate` lists them as WARNINGs). 12.5 beats of
free choice remain (the window opens at beat 48, the lock falls at 60.5).

## Arrangements (music library, M3)

A scene's `music.json` entry may name `"arrangement": "<id>"` (optional `"slot": k`, `"alternates": [ids of the same family]`) **instead of** `audio`/`chart`. The arrangement
(`content/music/arrangements/<id>.json`, built by `tools/content/arrange.py generate`, checked by `validate`; format in that file's docstring) is a list of sections of 8 or 16 bars, each a pack
(`pack`), a mix recipe (`content/music/mix_recipes.json`), fills and a role. A scene plays the 16-bar window `slot` of it (bars 16k+1 to 16k+16): one 16-bar section or two 8-bar ones. `RunData`
resolves that into `node.sections` (`{bars, role, pack, mix, gains, start_beat, beats}`), sets `node.audio` and `node.chart` to the first section's pack (**so the route lock compares the chart
pack of block 0 of the next scene exactly as before**) and exposes `chart_pack_at(scene, phase_beat)` / `section_start_at`.

* **Sound.** `RunAudio` schedules one item per later section at `phase start + start_beat * beat`: at that moment (same `now + time_to_next_mix` rule as a phase start) the old section's voices
  stop and the new pack's start `from` = how late the call is, so they sit on the grid; the clock stream is never touched, there is one voice group per section and no restart. The bass and synth
  start in the new section only when the bass has been revealed in this phase (otherwise at the reveal, from the section playing then). Gains are the phase mix's stage gain **times** the section's recipe gain
  (drums alone and the bass reveal stay the gameplay; a recipe never takes the bass under 0.5). The packs of every section are preloaded at the phase start. Fills are ignored in the run.
* **Charts.** `RunEngine._chart_block` takes the pack of the section playing at the block (`chart_pack_at`) and starts the bass/drum phrase with the section (`max(bass origin, section start)`); at the
  usual 16-beat blocks and 32-beat sections this changes nothing for scenes without an arrangement. Cue families per block stay the gameplay's.
* **Seed.** Same seed, same sections and chart. The per-run seed is `RunProgress.data["seed"]` (added on load to older saves, version stays 2; a new one is drawn each time a run starts),
  `RW_RUN_SEED=<n>` overrides it, and it picks between a scene's arrangement and its `alternates` by `hash("<seed>:<scene id>")`. `RW_RUN_MUSIC=<abs path>` makes `RunData.load_default` read another
  `music.json` (recordings and tools).
* **Checks.** `tests/test_run_audio_sections.gd` (resolution, per-block charts, the lock, the switch, the seed); a recording of the Warehouse on `warehouse_1` (`record_music.gd` +
  `tools/content/check_section_audio.py`): one drums voice per section, every block fitted within 0.01 of stage gain x recipe, 99.8 to 100 % explained, the second section's drums 2.9 ms from the phase's.
* **Chapters** play pre-rendered arrangements: `arrange.py render <arrangement> --bars N --chapter <id>` writes a mission-format pack (three stems the length of the chapter, `recorded_music` cues from the
  sections' tiers); `content/story/<chapter>.json` may list `"music_packs": [...]` (first = the chapter's own recording); `StoryRun.pick_music_pack` chooses by seed (none = the first).

## Saves and migration

`user://story_run.json` records every **world** (not scene) as *reached* the moment a phase starts on one of its scenes; the home screen's cards are worlds, and starting from a world (or retrying after a loss, or the pause
menu's "Restart this level") begins at the world's **entry scene** (its id is the world's id, so every old save and `RW_RUN_START=<world id>` keep working; any scene id also works as a start for tests).
Every level below means a world. Home shows **Start from a reached level** (locked cards say how a level opens),
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

The HUD is silent during play (see "The silent HUD" below): it no longer names the world, the room or the stage and shows no title card. Stages are keyed by art world (map), so the Hospital and
Hospital, late share one stage. World swap: the stage of each world is built once and kept; candidates for the next level are built during cue-free guards (one per guard) and the swap on the downbeat is a
visibility change plus a flash. Audio for the candidates is loaded on a thread when the route window opens. The old chapter scenes (`story_play`, `story_campaign`, `story_result`,
`story_interlude`) and the military screens still exist in the repository for the art pipeline, tests and the developer button (editor only), but nothing in the run path
or the home screen reaches them; the run path does not read the loadout, the library, the campaign rules or `Match`.

## Tunables

All numbers are data: `content/run/run.json` (`timing`, `judgement`, `energy`, `stages`, `mix`, `effects`, `treatments`, `worlds` depth, each scene's rail), `content/story/music.json` (a scene's pack),
`RunPassage.DOOR_BEATS` (3: when the door walk starts), `RunRail.MOVE_BARS_*` (2 to 4), `content/story/maps/*.json` (doorway and place waypoints). Longer or shorter worlds: add or remove a scene in
`tools/run/make_scenes.py` (`scene(...)` rows and the `PACK` table).

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

## Verification of the scenes (WP-A5, 2026-11-04)

* Suite: `--filter run_` 3555 checks and `--filter trial` 1224 checks, 0 failures; the full suite (57,226 checks) had one failure, an environment leak between my new scene tests and `test_trial`, fixed
  (`OS.unset_environment`) and re-run green by filter. `python3 tools/content/beatshaper.py validate` OK (16 sibling-chart WARNING lines: the route locks); `test_beatshaper.py` 20 tests OK.
* **Matrix** (`tests/test_run_matrix.gd`, 7 policies x seeds 1 to 3, 20 phases = scenes, the door walk simulated as the scene does): perfect, accuracy 0.9, 0.8, 0.7 and sloppy survive all 20 phases and reach
  depth 4 through 4 to 6 worlds and 16+ distinct scenes (perfect: 20 phases, 38 up steps and 42 top, never the bad rail); accuracy 0.5 ends after 6, 8 and 13 phases (depth 2, 2, 3); no play ends in phase 2 in the
  Warehouse at the sick beat on every seed. Every step is a route of the scene before it; every move starts in a guard, lasts 2 to 4 bars and sits on no dense cues; the camera is always in a valid sector.
* **Walk** (`tools/run/walk_run.sh`, real scenes, virtual clock, isolated save): perfect_a to perfect_d visit 19, 17, 17 and 17 scenes; together with sloppy, none and start_late all **36 of 36 scenes**; the save has
  worlds only. Result `run walk-through: OK`. (The Ward world's missing source art, below, prints resource ERRORs; the walk was run with `RW_WALK_IGNORE='assets/story/mental_hospital|\.godot/imported'`.)
* **Recording** (`record_music.gd` 70 s on `run_play.tscn`, Warehouse, perfect, routes right,right: floor > bar > chill-out; `check_run_audio.py`): three phases `warehouse` (`lv1_warehouse`), `warehouse.bar`
  (`lv1_warehouse_v1`, entered on a path change inside the world), `warehouse.chill` (`lv1_warehouse_v2`): every block fitted within 0.01 of the stage's gains, 99.8 to 100 % explained, one drums voice per phase
  entered on the grid, bass and synth 0.0 to 2.9 ms from the drums, no restart; delay per phase -46.8, -41.0, -38.0 ms (spread 8.8 ms, a little over the 5.9 ms mix chunk, the same slow drift the WP-A1 note
  measured, not tied to the path change: phase 1 to 2 moved 5.9 ms, 2 to 3 3.0 ms), RESULT CHECK because of that spread. A first recording taken while a walk was running showed one riser missing in phase 3
  (the machine was loaded); the repeat was clean.
* **Frames** (`tools/run/frames.sh`, 1280x720 windowed, vsync off, perfect, `RW_RUN_UNTIL_PHASE=3` = three scenes including two door walks, an otherwise idle machine, Intel HD 520): Warehouse 5500 frames mean 12.1 ms p95 15.5
  max 62 (1 over 50 ms); Mothership 4976 mean 13.4 p95 18.1 max 47 (0); Underworld 4908 mean 13.6 p95 17.9 max 47 (0); Hospital 4820 mean 13.8 p95 17.9 max 36 (0). A door walk builds nothing (the stage stays); only a world
  change builds a stage (Warehouse 333 ms, Mothership 1.3 s in the first guard, once).
* **Screenshots**: `docs/shots/run/node_<scene>`, `route_<scene>` (the route window with the lit doors, labels wrapped), `doorwalk_before` / `_through` / `_arrived`, `doorwalk_mothership_reactor`,
  `doorwalk_hospital_corridor`, `passage_*`, `journey_*`, `rail_warehouse_*`. Shot for the Warehouse, Mothership, Underworld, Hospital, Hospital late scenes; **the Ward and Ward, late scenes were not shot** (see below).
* Not done: nothing was listened to or played by hand; the Ward worlds were exercised headless and in the walk only. The Ward chapter's source SVGs (`assets/story/mental_hospital/source`) and part of the Night
  One manifest were missing in the branch this work started from (fixed on `feature/run-on-25d`, commit 4d2e8525, not here); the determinism check of `tools/story/check_assets.py` was skipped.

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

## Rails and activities in the run (WP-A3; "node" there is now a world's scene, see the scenes section above)

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
* **Route window.** The window is the hotspot window (see "Hotspots" below): the room's exits are lit by `HotspotView` (a door ajar at the waypoint of each route, or a beacon at the screen edge when it is out
  of sight), touched in the world; there are no arrows and no labels (the old arrows and `RunExitsView` are gone).
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

## Hotspots (workstream A of the visual rhythm adventure)

The route window is the **hotspot window**: no arrows, no labels, no `[DEFAULT]`. The player touches the world; the music never stops and the pads stay the only other input. Contract and plan:
`docs/VISUAL_RHYTHM_ADVENTURE_PLAN.md` (section 2), the owner's brief `docs/VisualChoicePlan.md`. The old arrows, lit-door view, labels and the wizard's "Enter the Trial" button are
removed for good (the Bassment's conversion has landed: `TrialScene` draws and hit-tests with the same `HotspotView`).

| Piece | File | What |
| --- | --- | --- |
| Contract | `src/run/hotspot_contract.gd` | field names, vocabularies, the validator both data loaders call (`HotspotContract.validate_scene`), `normalize`, `resolve_cinematic` |
| Data | `RunData` (`content/run/hotspots/<world>.json`), `TrialData` (`content/trial/hotspots.json`, passage-keyed) | loaded, normalised, validated; a run scene with no authored hotspot gets one exit per route from `rail.exits` (the first the default), so the run is always playable |
| Engine | `src/run/run_hotspots.gd` (pure) | availability, selection, commit, outcome, world state |
| View | `src/run/hotspot_view.gd` | drawn inside the low-res viewport above the crowd (`StoryLowRes.add_overlay`, canvas layer 2); pure `layout` and `hit` |
| Scene | `RunPlay` | taps, keys, the wizard, outcomes to `RunEngine` / `RunJourney` |

**Windows and commit.** The *final* window (any exit, object, character ...) opens with the route window (beat 49) and commits at the decision beat of the last block (beat 60.5 to 60.75, inside the
cue-free guard, exactly the old route lock). The *early* window belongs to a hotspot whose success route is a Bassment passage (`"1"` or `"trial:1"`, the wizard): it shows in blocks 1 and 2 only and
commits at the next block decision (two guards are needed to arm the entry). Selection changes freely until the commit; after it nothing can be selected. At the commit the block just judged decides:
**passed -> `on_success`, missed -> `on_failure`**. Nothing tapped: the scene's default exit whatever the performance (no intent, no failure). The route of the outcome (or, for an outcome with none,
the scene's default route) becomes `RunEngine.choice` *before* the next phase's first block is charted, so the chart pack is always the resolved route's: there is no late swap and the route lock
only ever sees the resolved outcome (the five diverting outcomes of the data chart the right pack). `RunEngine.hotspots == null` keeps the plain route choice (engine-level tests and the scripted `RW_RUN_ROUTES` bot only; the scene always has hotspots).

**World state.** `flags_set` names go to `RunProgress.run_flags` (one run, cleared by `run_started`) or, with the `keep:` prefix, to `RunProgress.flags` (persistent, in the save, written at once).
`available`: `flags_all`, `flags_none` (both read both stores), `energy_min`, `once` (spent by any commit this run). `repeatable: false` (the default) spends an object/character after a *success* without a
route; exits and `repeatable: true` are never spent. Energy outcomes apply at the commit (never to depletion: clamped to at least 1); `music` ("variation", "dip") rides on the `hotspot_commit` event
for the audio layer: `dip` sinks the non-drum voices to `mix.dip_gain` of their gain (0.55; 0.35 before the audio polish) for `mix.dip_beats` beats (6; 8 before) from the commit beat (`RunAudio`, through the existing gain ramps); `variation` is a documented no-op (a scene's arrangement is picked
by the per-run seed when the data loads, and re-picking it for the next scene would change that scene's chart pack after the route lock compared it). `challenge` is validated and carried but not consumed (the last block decides).

**Cinematics.** An outcome's `cinematic` is a name in run.json `cinematics` (`{world, steps: [{move: walk|place, to, bars 2..4, role, style, look_at}]}`), else the hotspot's own `cinematic` spec, or an
inline object. `RunJourney.hotspot_actions` turns steps into rail actions starting at the commit beat (in the guard): `walk` a `player_move` (pick_bars shortens it on dense cues), `place` a cut, `role`,
`look_at` a `player_look` toward the target. An outcome with a *route* keeps the door walk as the camera's move (only roles and looks are applied; a step's style becomes the door walk's style: an exit
failure staggers through the same door). An outcome that simply *continues* by the default exit plays the move instead of the door walk (`_door_phase` is latched), and the next scene's door walk waits
for it to end if that is within 6 beats.

**Acting.** A hotspot may carry an `acting` block (what its person does while it waits, when touched, at the commit and after the result), and scenes and cinematics may carry `cast` lines: see "Acting in the run" below.

**Taps.** `RunPlay._input` takes a press (touch or left click; an emulated duplicate within 80 ms and 3 px is dropped) and calls `hotspot_tap(pos)`: only the stage area counts, a point over a pad is
never a hotspot, then `HotspotView.layout` projects every hotspot on show through `StoryProjector` at the stage's screen size and `HotspotView.hit` picks the **nearest centre within its own radius**,
where the radius is the projected `radius_m` but never under `min_px / 2` (so a target is at least 72 px wide), clamped so the whole target lies inside the stage view (never over the pads). An anchor
out of sight (behind the camera, round a corner) is a **beacon** of light at the edge of the picture on the side it lies, stacked down the edge, still touchable (free look is never required).
Desktop: keys 1 to 4 select the hotspots on show in order, the arrow keys the one that leads that way.

**Looks** (no text, no floating rectangles): available = a ring of light on the floor under the anchor (a perspective-correct ring projected point by point) and a glow on the thing, slowly pulsing; the
`look.available` value picks the character: `glow`, `pulse` (one pulse a beat), `beckon` (a light column with a mote riding it; an actor anchor also *waves* through `StoryCrowd.beckon`, even a bartender
with a fixed activity), `flicker`, `open` (a slit of light standing at the doorway, spilling on the floor), `crack` (a glowing crack in the floor). The **default exit** is brighter, has a second ring and
its door stands wider ajar. Selected = a bright ring, a second ring closing in, a lift of the glow and a spark; committed = a flash, the ring opening out, the glow surging (about half a second).

**Joining any block (`window: "any"`, `pass_credit`, the "claim" look).** A hotspot whose `on_success` has an `activity` (the blackjack table) may say `window: "any"` (default `"final"`): it is on show in every block of the phase until
a final commit has happened, and a touch in block 0, 1 or 2 commits at that block's decision beat (`RunHotspots.on_block`, the block's credit passed in by `RunEngine._hotspot_decision`). Success is the activity outcome (`route` = the scene, `stays`:
the run holds here; the player is seated at the end of the block just judged, `RunPlay._on_hotspot_commit`); failure is `on_failure` with no route and no camera move. An "any" hotspot never latches `committed`, so it can be touched again after a wave-off
or after getting up, and the scene's default exit still commits at the final as ever (in block 3 it commits like any final hotspot). `pass_credit` (0 to 1, only with an activity) makes it succeed when the judged block's credit is at least that,
instead of the run's pass (0.6): the table uses 0.25. `radius_m` is the touch radius, `look.ring_m` the radius of the ring that is drawn (default `radius_m`), so a generous target does not draw a giant ring. `look.selected: "claim"` is the table's look: a burst
at the touch (floor flash, a thick ring flying out, a wash round the picture's edge), then light filling the floor disc, a thick ring throbbing on every beat, a tall beam, and a second ring closing in from outside that lands on the first exactly at the decision
(`t_commit` on the `hotspot_items()` entry); seated = a bigger flash, waved off = cold grey light, the ring breaking into segments that drop, a short shake. Reduced motion: no throb, burst or shake, the countdown is an arc filling clockwise.
`on_select: {"cinematic": name}` is a walk the touch itself starts (the table's `ward.cards_approach` to the chair): `RunPlay._on_select_walk` plays it at the touch, the rail's block steps are held meanwhile, the sit cinematic skips a move to the same waypoint,
and a wave-off, or touching another hotspot, gives the camera back to the rail with `RunPlay._back_to_rail` (the same restart-and-walk-home the end of a minigame uses).

**Tests.** `tests/test_hotspots_data.gd` (the contract and every rule), `test_hotspots_engine.gd` (availability, selection, windows, commit, outcomes, flags, determinism at 30 / 60 / variable frame
steps with scripted taps at song times), `test_hotspots_view.gd` (projection, 72 px, nearest, beacons), `test_hotspots_scene.gd` (the real scene: view in the viewport, tap/change/commit beat,
default, failure, cinematic as the move, wizard arms or shrugs, keys, the flag), the touch-target test in `test_run_scene.gd` (844x390: on the stage, 72 px, never over the pads) and the matrix's tap
policies. **Tap policies** (`RW_RUN_TAPS=scripted|none|changed|failure`, `tools/run/walk_run.sh` and `tests/test_run_matrix.gd`): `scripted` taps the hotspot toward the path's route at beat 52, `none`
never taps, `changed` taps a decoy at beat 50 first, `failure` taps and misses the last block of every phase. `RW_RUN_SELECT=<hotspot id>@<beat>` touches one hotspot (screenshots:
`tools/run/capture.sh`, `hotspots_*`: before, selected, committed, success, failure, wizard, phone).

## Acting in the run: hotspot `acting`, scene `cast` and cinematic `cast` (docs/THREE_PATHS_AND_FACES_PLAN.md 2.3, stage 1b)

People are told what to do and what to feel by data, never by text.

- **`acting` on a hotspot** (`content/run/hotspots/<world>.json`; validated by `HotspotContract.validate_acting`): `{actor?, available?, selected?, committed?, success?, failure?}`, each state
  `{act, face?, look_at?, beats?, then?}`. `actor` defaults to the anchor's actor and may be named on a thing or waypoint anchor (the bouncer by the door). `look_at` is `camera` or the id of an actor,
  a thing or a waypoint of the scene's map (`HotspotContract.look_ok`). `beats` is how long an outcome act holds (8 by default; a `then` holds 16 unless it says), `then` is what the person settles into.
  Acts are the fifteen directed ones plus the older states (`HotspotContract.ACTS`, built from `StoryCharacter.ACTS` and `DIRECTABLE_OLD`); faces are `StoryCharacter.FACES`. The pure helpers are
  `RunActing`: `available_spec` / `selected_spec` (a hotspot with **no** `acting` block keeps the old `wave` at the player, so nothing shipped changed), `outcome_chain` (the `committed` act for two
  beats, then the success or failure act, then each `then`, end to end from the commit's song time).
- **Who plays it.** `HotspotView._manage_acting` tells the crowd the `available` act while the hotspot waits and the `selected` act once touched (`StoryCrowd.direct_actor`, forced, so a bartender or a
  bouncer obeys), and stands its own act down when the hotspot leaves. `RunPlay._act_outcome` plays the commit's chain (`StoryCrowd.direct_chain`, source "outcome") from the `hotspot_commit` event's song time.
  A story beat already in force on a person (source "cast") is not interrupted by an `available` act; a touch always is. Divergence from the plan: the plan calls the new crowd call `direct`; that name is
  the crowd's group directive (twenty callers), so it is `direct_actor(id, act, face, t0, until, look_at, src)`.
- **The crowd's `dir`** carries `state`, `from`, `until`, `sync`, `force` and now `face`, `look_at`, `src` and `chain` (the segments still to come). While it is in force `StoryCharacter.face_override` is
  the face (so `sheet_pick` chooses `act@face` frames when the person was baked with them, else the act's own) and a live `look_at` turns the person toward the target (`StoryCrowd.look_point`:
  `camera` is the eye, so they face us; an actor, a thing or a waypoint is its ground position; it also decides the arm of a `point`).
- **`cast` on a scene node of `run.json`**: `[{actor, at_beat, act, face?, look_at?, beats?, if_energy_below?, if_energy_above?, if_flags_all?, if_flags_none?}]`, `at_beat` 0 to 63 of the scene's phase (0 to 64 x laps - 1 for a scene of a path that plays several laps, counted from the scene's first downbeat).
  `RunEngine` queues the lines when the scene begins and emits one `cast` event per line at `phase_t0 + at_beat * beat_s` (`t` is the line's own time, whatever the frame step; ties in file order; a
  line due on the same instant as a block decision goes first, so its conditions read the energy as it stood at that beat). Conditions read the crowd's energy and the world-state flags (run or `keep:`) at
  that beat; a line whose conditions fail emits nothing. A stall across several lines fires them all, in order. The lines of a scene left before they came due are dropped.
- **`cast` on a cinematic** (`run.json` `cinematics.<name>.cast`, the same lines with `at_beat` 0 to 16 relative to the commit): the outcome's cinematic carries them (`HotspotContract.resolve_cinematic`),
  `RunEngine` queues them from the `hotspot_commit` and they play on if the scene changes; `RunPlay._on_cast` acts them in the world the cinematic names.
- **Checks**: `RunData._validate_casts` validates every scene's and cinematic's lines against the scene's map (a person with a home in it, a known act and face, a look target, `at_beat` in range, no stray
  field: nothing can carry text). `tests/test_run_cast.gd` (events, order, beats, conditions, determinism at any frame step, no cast = unchanged, cinematic cast, validator, the crowd's face and look),
  `tests/test_hotspots_engine.gd` (acting leaves the outcomes alone, chains, validator, every shipped hotspot both ways). `tools/story/art/directed.py` reads hotspot `acting`, scene `cast` and cinematic
  `cast` so the sheets bake exactly the acts and faces the data names (`tools/content/test_directed.py`).
- **Authored (stage 1d, 5 November 2026)**: every character hotspot with a person to direct (28 of the 30, the two wizards are billboard things; plus the Warehouse stranger) carries an `acting` block with all five states, every one of
  the 36 scenes carries 2 to 4 `cast` lines (blocks 0, 16, 32, 48, a few conditional on energy: `if_energy_below` 35 to 50 for the people who react to a played-out player, `if_energy_above` 55 to 85 for the ones who
  celebrate) and 16 existing setback and success cinematics carry acted reactions of the people around. The tables are `tools/run/acting_data.py` (`ACTING`, `CAST`, `CINE_CAST`); `make_hotspots.py` and `make_scenes.py`
  copy them into the generated `content/run/hotspots/<world>.json` and `content/run/run.json`, so edit the table and rerun `python3 tools/run/make_scenes.py`. The hotspot windows decide when an act is seen: a final-window
  hotspot is on show from beat 48 (available, then selected once touched), commits at 60.5 (the committed act for two beats, then the result for `beats`, about four of which are seen before the next room), so a
  bystander's reaction to a result in a scene whose outcome has no cinematic is a `cast` line at beat 61 to 63 conditional on the flag the outcome sets (`if_flags_all`). Only the acts and faces the data names are baked
  (`content/story/directed_actors.json` is empty now). Proof shots: `bash tools/run/capture.sh --acting` (`docs/shots/acting/`, a strip of the five states per person and a contact sheet per world; `RW_STORY_CAM=actor:<id>:<m>:<pitch>`,
  `RW_RUN_CLEAN=1` and `RW_RUN_FLAGS=a,b` are its screenshot aids). Tests: `tests/test_run_cast.gd` (every shipped scene line fires once at its beat in a perfect and in a missed phase, every energy condition holds at its beat,
  every cinematic line fires after its commit, 28 people hotspots act in all five states), `tests/test_story_acts.gd` (the sheets bake exactly the directed people and their acts and faces).

## The silent HUD (docs/THREE_PATHS_AND_FACES_PLAN.md D3 and 2.4, stage 1c)

During play nothing is written: no title card, no HUD captions (BASS ENTERS, RISER, FALL, HOLDING THE MIX, THE CROWD DRIFTS AWAY), no world or room name, no stage label, no "CROWD" label, no numeric
countdown, no DRUMS / BASS banner and no "CROWD" caption on the pads, no "Nice: the mix moves on" status line, and in the Bassment no title, caption band, zone tag or banner (YOU DIED, VICTORY, DEFEATED). What stays: the four
mix pips, the energy meter, the pads' judgement words (PERFECT, GREAT, MISS: feedback, not story), menus, the pause panel, settings, the result screens and the F3 line. `RW_DEV_TEXT=1` (`DevText.on()`, read
at call time) brings all of it back, and the tests that read captions or title cards set it (`test_run_scene`, `test_trial`).

The information the text carried is in the world: BASS ENTERS is the bass coming in with the lights lifting, ROUTE CHOSEN the hotspot's committed flash, RISER / FALL are audible, and a new room is the door
walk plus a **light swell**: `StoryStage` action `room_swell` (RunPlay sends it on every phase start but the first) lowers the room's lamps to 55 % on the downbeat and brings them up over two beats
(`StoryStage.swell_gain`, `StoryWorld.light_of` ctx `swell_gain`). The choice window is a thin gold bar along the bottom of the picture that empties over the 16 beats (`RunHud.window_left`), the same
bar the Bassment's four-bar window uses.

The Bassment's 63 passages' narrative is acted by the creature standing in the room: `content/trial/hotspots.json` encounters carry `acting: {figure, available, selected, success, failure}` authored from
one table keyed by creature kind in `tools/trial/make_hotspots.py` (`CREATURE_ACTING`; the contract's `figure` names a creature instead of an `actor`). A creature is a billboard, not a baked person, so its
acts are motions on the figure (`RunActing.figure_motion`: block, offer, laugh, stamp, recoil, bow, collapse, shake_head, nod, plead, stare), played by `TrialScene._animate_figure`: the `available` act
while it waits, `selected` once tapped or while the fight is on, `success` when it is beaten, `failure` when it beats you. Items, exits and luck tests have no acts (their lights are the look).
`tests/test_run_hud_silent.gd` hooks `RunHud._outlined` (a counter, `strings_drawn`) over a scripted run from the count-in through the second scene; `test_trial.gd` checks the Bassment's text is hidden.
Before/after shots: `bash tools/run/shoot_silent.sh` writes `docs/shots/silent/`.


## Paths: sister runs at their own tempo (docs/THREE_PATHS_AND_FACES_PLAN.md section 3, stage 2)

A path is a second run beside the 174 BPM one: its own `run.json` (`timing.bpm` 124 / 140 / 145), `music.json`, hotspot files and packs, played by the same `RunEngine`, `RunAudio`, `RunPlay`, `HotspotView` and
stage code. The 174 run is not changed (it never loads a path's pack, validates exactly as before and its scenes behave as before). The proof path is `stub` (two scenes at 124 BPM on the Warehouse's own art,
synthesised placeholder music, `dev`: listed on the home screen only once reached); the three real paths are `gospel` (The Life of Jesus, house 124 BPM, 17 scenes in 4 worlds, music still placeholders), `squadron` (The Mission Count,
dubstep 140 BPM, 14 scenes in 4 worlds, on the owner's own loops) and `ember` (The Ember Road, psytrance 145 BPM, 15 scenes in 5 worlds, placeholders). Per-path notes with the scene tables, flags, art and checks:
`docs/paths/gospel.md`, `docs/paths/squadron.md`, `docs/paths/ember.md`; the whole project's state: `docs/HANDOVER.md`.

```
content/paths/<id>/run.json        "path": {id, title, entry_from, returns_to: "warehouse", opens, laps?, dev?}, timing.bpm, worlds, nodes, cinematics (judgement, energy, stages, mix, effects, treatments are the main run's unless the file says otherwise)
content/paths/<id>/music.json      one entry per scene (audio / chart pack, "temporary": true for placeholders); "placeholder": {genre, key, levels_db, sub_hz, ...} = the mix of the synthesised stand-ins
content/paths/<id>/hotspots/<world>.json     the path's hotspots (the same contract; an ending's default exit sets keep:path_<id>_<ending>)
content/paths/<id>/walks.json      (optional) extra walks for tools/run/walk_run.sh --path
songs/packs/<id>_<scene>/          the path's packs, pack.json carries "path": "<id>" (the main run never loads it; the path's run loads only its own) and its BPM must equal the path's
content/imports/<id>/<scene>/      the owner's drops (git-ignored: large); a scene with a drop never gets a placeholder
```

**Data rules** (`RunData`, when run.json carries `"path"`; `RunData.load_path(id)`, `load_default()` is the Warehouse run): a world may have several entry scenes (its own id stays one of them) and several exit
scenes; routes to another world's entries are allowed from any exit scene; the graph is acyclic except through `loop` routes; every scene must reach an **ending** (`"ending": "<name>"`, whose one route is
`run:warehouse` and whose default hotspot sets `keep:path_<id>_<name>`); a pack at another tempo than the path's is refused; a path never leads into another path or the Bassment. The Warehouse run keeps its strict rules.

**Portals.** `warehouse.balcony.star` (`path:gospel`), `warehouse.booth.radio` (`path:squadron`), `warehouse.bar.ember` (`path:ember`) are `secret` hotspots with `look.available: pulse`, never the default,
`repeatable`; success routes `path:<id>`, failure flickers out (-4 energy, no route: the scene's default exit takes over). They count in the 2 to 4 rule: the star appears once the floor has been seen from the rail
(flag `wh_saw_floor`, set by the balcony rail hotspot's own success, which is then spent), the ember once the stranger's VIP pass is taken (`wh_vip_pass`), the radio always (the booth has room). All three paths now
exist, so all three portals are live in the shipped Warehouse (`RunData` still leaves a portal out of play, logging `RUN portal ... is hidden`, if its `content/paths/<id>/run.json` is missing). `RW_PATH_REMAP=gospel=stub` plays the stub
through the star. **Gating flags in one table:** star `wh_saw_floor` (the player must have looked at the floor from the balcony rail first), radio none, ember `wh_vip_pass` (the stranger's VIP pass); `RW_RUN_FLAGS=wh_saw_floor` /
`wh_vip_pass` set them for a test or a review. Not built (plan D10): the Warehouse portal showing a different look once a path has been finished (the flags `keep:path_<id>_<ending>` are set and saved; nothing reads them yet except the
home screen's "Endings found: N").

**The tempo handoff** (`RunEngine._commit`, `RunPlay._path_swap`, `RunAudio.schedule_clock_swap`). When the phase ends on a `path:<id>` (or `run:warehouse`) route the engine emits `path_handoff` instead of
entering a scene and freezes (`away`). The passage frame closes over beats 62 to 64 as for a world change. On the downbeat: `RunAudio` replaces the clock stream (one scheduled item, before the new phase's
voices) by the 64-beat silent loop of the new tempo (`silent_loop`; the rate makes a beat a whole number of frames: 8680 Hz at 124, 8400 at 140, 8700 at 145 and 174; `RunAudio.frames_per_beat`), the song time
stays one unbroken line (`song_base` becomes the downbeat, the wrap count restarts; the old loop's length is used until then because its last wrap is this downbeat), and the old voices fade through the usual
phase change; a **new `RunEngine` / `RunHotspots` / `RunJourney`** of the other run begins its start scene on drums alone with `arrive(start, t0, energy, phase_n)`: its beat grid starts on that downbeat
(`grid_origin`: cue times are `grid_origin + tick * 60 / (bpm * 960)`, so they sit on sixteenths of the new beat counted from the downbeat, not on the old grid), the crowd's energy and the phase count are carried
over. The pads, note lane, HUD, hotspot views, `StoryStage.set_tempo` and the stage's `proxy.level` follow the new engine (the pads and the judge read the active engine's `beat_s`). The way back (`run:warehouse`
from an ending, or the pause menu's **Leave this path**, taken from beat 61 of the phase) is the same swap in reverse into a fresh Warehouse engine with a fresh rail (the camera steps in through the door as for
a world change; energy carries). A path that cannot be loaded does not strand the run: the Warehouse goes on by its default exit. `RW_RUN_PATH=<id>` starts a path directly (`RW_RUN_START` names its scene);
`RW_RUN_PORTAL=<hotspot id>` makes the bot touch a portal, `RW_RUN_FLAGS=a,b` sets world-state flags after the run starts.

**Save and home.** `user://story_run.json` gains `paths: {"<id>": {"reached": [worlds], "endings": [names]}}` (added on load to older saves, version stays 2; a path's worlds never enter `reached`). Start from a
reached level lists each path that has data under its own heading once one of its worlds is reached; a locked card says how the path opens (`path.opens`); a `dev` path (the stub) is listed only when reached.

**Placeholders.** `python tools/content/make_path_placeholders.py <id>` writes, for every scene with no import, `songs/packs/<id>_<scene>/`: 8-bar loops (32 beats) of drums, bass and a pad as 48 kHz stereo WAV of
exactly `loop_frames` (not Ogg: that is the format `beatshaper.py import` writes and Ogg cannot guarantee a sample-exact loop) plus the MIDI they were made from (`midi/*.mid`), charted through beatshaper's own
`build_cues` / `tier_cues`, `"placeholder": true`, `temporary` in music.json. Genres: house (four on the floor, claps on 2 and 4, offbeat open hats), dubstep (half time, sub with a wobble), psytrance (a 16th-note
rolling bass between the kicks). The mix is **bass-forward and lives in music.json** (`placeholder.levels_db`: RMS dBFS of each stem, default drums -20, bass -13, pad -27; the generator refuses a bass that is
not 8 dB over the pad and louder than the drums, or whose sub share (under `sub_hz`) is under `sub_share_min`). `beatshaper.py --path <id> <command>` does the owner's imports at the path's tempo (profile
`<id>_x1`, `--bpm` for a path whose run.json is not written yet, `--max-error-ms` for a deliberate, recorded loosening); see `docs/MUSIC_IMPORT.md` section 7.

**Checks.** `tests/test_run_paths.gd` (rates, data and relaxed rules, wrong-tempo pack, portals both ways, save migration, the engine handoff in both directions with beat_s before and after, the phase on the
downbeat and the cues on the new grid, the audio clock swap, the real scene entering the stub through the balcony and leaving by its ending, starting in a path and leaving by the menu), the per-path matrix in
`tests/test_run_matrix.gd`, `tools/content/test_paths.py`, `python3 tools/run/check_hotspots.py --path <id>`, `bash tools/run/walk_run.sh --path <id>`, and the recording of a handoff
(`tools/story/record_music.gd` on `run_play.tscn` with the variables above, then `tools/story/check_run_audio.py`, which reports the measured beat grid per phase and at each handoff).


### The three real paths: what the stages added to the engine (stages 3 to 5)

* **Graph rules** (`RunData`, only when run.json carries `"path"`): beyond the stage 2 relaxations, a path's exit scene may lead on inside its own world and to a non-entry scene of it (`is_path()` relaxes the checks; the Gospel's J05, J06 and J07
  route within `galilee`); the depth rule of exit scenes (one level deeper) is lifted, because a setback goes back to an easier world (Squadron's C04, C06, C07, C11, Ember's setbacks); scenes entered from another world are `entry` scenes (several per
  world); a route that goes back is `loop: true` where the validator wants it (Squadron C05 -> C06, C07 -> C10, C11 -> C12, the C11 -> C02 absurd loop, the cell, Ember's Taken and the Birch Hall setbacks). `tools/run/check_hotspots.py --path`: a route needs
  *some* hotspot (a feature, an object, a person, any kind) that leads to it, not an exit of its own; the main run keeps the strict rule.
* **Maps and worlds**: a world has one map, but several worlds may share one (`base` and `air` on `airfield`, `marsh` and `mountain` on `ash_land`); a world names its story data with `"story": "res://content/story/<map>.json"` (`RunPlay._story_entry`), so a
  path's maps are never chapters of the Story chapters menu. A path's first stage is built in a cue-free guard (`RunPlay._prebuild_in_guard`, `_prewarm_routes`; `build_log` records phase and scene), so the stage a portal opens on is not built behind the
  closed frame. A sector may name its own `sky` and `fog` (`StoryMap`, `StoryWorld.set_atmosphere`, applied by `StoryStage` when the camera's sector changes): one map holds a night room and a dawn one.
* **Set pieces** (`HotspotContract.validate_pieces`, `RunPlay._apply_pieces`, `RunPlay.piece_log`): a map thing with `"piece": "<id>"` is shown while it is on. A scene node may carry `"pieces": {"on": [...]}` (listed pieces are on from the downbeat, every
  other piece of the stage is off), an outcome `"pieces": {"on": [...], "off": [...]}` (applied at the commit), and a scene `"block_fx": [{"block": 0..3, "pass": {pieces?, cast?}, "miss": {...}}]` (applied at that block's boundary; cast lines use `at_beat` 0).
  The Gospel's Golgotha is staged this way (the sky darkens every block; a passed block brings a witness forward, a missed one a laughing soldier). Validated by `RunData._validate_stage_fx`.
* **Cast lines** (`HotspotContract.CAST_KEYS`): besides the acting lines of "Acting in the run", `{"piece": "<id>", "op": "on|off|pulse", "at_beat": n}` switches a set piece, `{"actor": "<id>", "hide": true, "at_beat": 0, "if_flags_all": [...]}` removes a person
  from the scene (`StoryCrowd.hide_actor`: Bram when you are alone, the Warden once he has fallen); cinematic `cast` takes them too. `RunPlay._on_cast` calls `StoryCrowd.ensure_present`, so a cast line brings its person in (the grove's traitor and guards are group `late`).
* **A path's own mix**: a path's run.json may carry its own `stages` (Squadron's four laps of its 16-beat loop: drums alone; drums 0.7 + bass 1.0; drums 1.0 + bass 0.9 + synth 0.5; drums 0.55 + bass 1.0 + synth 0.7). A 4-bar loop tiles the 64-beat phase four times, so each
  16-beat block is one lap and brings a new layer. Gospel and Ember use the main run's stage table.
* **Flags**: endings and meetings are `keep:` flags (`keep:path_gospel_tomb`, `_road`, `keep:path_squadron_free`, `_clause`, `_met_*`, `keep:path_ember_quenched`, `_kept`); per-path run flags are prefixed (`sq_*`, `ember_*`, `gospel_*`) and cleared with the run. Ember's flags change later scenes
  (`ember_no_vial` swaps E09's plain bells for the hard bells, `ember_warden_lost` and `ember_alone` take companions out of later scenes by `hide` lines); see `docs/paths/ember.md`.
* **Environment variables** (all read by `RunPlay`): `RW_RUN_PATH=<id>` starts a path directly; `RW_RUN_START=<scene id>` names the start scene (of the path with `RW_RUN_PATH`, otherwise of the main run); `RW_RUN_PATH_START=<scene id>` names the first scene when a path is
  entered through its portal; `RW_RUN_PORTAL=<hotspot id>` makes the bot touch a portal in the final window; `RW_RUN_FLAGS=a,b` sets flags after the run starts; `RW_PATH_REMAP=gospel=stub` plays one path through another's portal; `RW_DEV_TEXT=1` brings back the play text of
  the silent HUD; `RW_RUN_SELECT=<hotspot id>@<beat>` selects a hotspot at a beat (tests, shots); `RW_RUN_CLEAN=1` draws no notes and no HUD (acting shots); `RW_STORY_CAM=actor:<id>:<m>:<pitch>` frames a person (acting shots).
* **Tools**: `bash tools/run/walk_run.sh --path <id> [walk ...]` (the walks come from `tools/run/path_walk_spec.py` plus `content/paths/<id>/walks.json`; on Windows set `GODOT` to the console binary, the script's default is the Linux one);
  `python3 tools/run/check_hotspots.py --path <id>`; `python3 tools/content/beatshaper.py --path <id> validate|scan|survey|check|import|apply [--max-error-ms N]`; `python3 tools/content/make_path_placeholders.py <id> [--force]`;
  `godot --headless --path . -s tools/run/check_path.gd -- <id>` (a path's data) and `-s tools/story/check_map.gd` (a map and its chapter); shots: `bash tools/run/capture_path.sh <id> [--acting]`, `tools/run/shoot_gospel.sh`, `tools/paths/shoot_squadron.sh`.
  Authoring: `python3 tools/content/make_gospel.py`, `python3 tools/paths/make_squadron.py`, `python3 tools/run/make_ember.py` (each writes the path's run.json, hotspots and walks from its tables; edit the table, rerun).
* **Save**: `user://story_run.json` has `paths: {"<id>": {"reached": [...], "endings": [...]}}`; a path's worlds are never in `reached`.
* **The tempo handoff and the song clock**: the first phase change inside a path used to sit 88 ms off (a new stream's position reads one mix period ahead after its first mix, so the clock ran ahead of the sound after every swap). Fixed in `56adc157`: `RunAudio._swap_clock` sets `song_base = t - mix_period(ttnm)`,
  `clock_log` records the period, `tools/story/check_run_audio.py` asserts every in-path phase boundary within 29.4 ms (the dummy driver's floor). Measured with the dummy driver only.


## Two laps per path scene (docs/HANDOVER.md A12)

The audio polish (A10) found that the three paths' music turned over every phase (Gospel 31.0 s, Squadron 27.4 s, Ember 26.5 s), so the player never sat in a song. A scene of a path now plays its music and its
staging for **two consecutive 64-beat phases ("laps") before the route commits**. The 174 BPM main run keeps one (and behaves, validates and tests exactly as before). (In `docs/paths/squadron.md` "lap" also names
one repeat of the 4-bar loop inside a phase; here a lap is a whole 64-beat phase.)

**Data.** `path.laps` in a path's `run.json` is the default of every scene of the path (1 when absent); a scene node may carry its own `laps`, which wins. A whole number from 1 to `RunData.MAX_LAPS` (4); only a
path's scenes may play more than one (the main run refuses it) and a scene that plays an arrangement (the main run's two sections per phase) plays one. Shipped: `path.laps` 2 in `gospel`, `squadron` and `ember`;
`"laps": 1` on **J00 `jordan`** (the prologue: a night road, one way on; a minute of it before the first story scene would be a wait, not a song), **J14 `jerusalem.golgotha`** (the sky darkens one step a block and
a witness or a soldier steps forward a block: one descent, a second lap would only repeat it; its `block_fx` and its cast are authored for one pass) and **E00 `hollow`** (the orchard prologue, one way on). Every
other scene takes two, **the endings included** (J15 tomb, J16 road, C13 quay, E12 spring, E13 keeper): the finale is where the player most wants to sit in the song, and the ending's flag is still set by its
default exit at the end of the last lap. `stub` stays at one. `RunData.laps_of(scene)`.

**What a lap is.** Each lap is a phase of the engine: its own phase number (`phase_n` counts laps; `RunEngine.scene_index()` = `phase_n - lap_extra` counts scenes), its own four blocks, cues and judge results,
its own `block_result`. The per-block rules are the single phase's, untouched: the tap windows, the pass credit, the energy gain and loss of a block, the 16-beat blocks, the 12-beat cue span and the decision at
12.5. `RunEngine` has `lap`, `laps`, `scene_t0` and `lap_extra`; `phase_start` carries `lap` (1), `laps` and `lap_extra`; `block_result` and `route_window` carry `lap`. At the end of a lap before the last the
engine does not commit: it emits `lap_start` {node, lap, laps, t, phase, stage, lap_extra, scene_t0} on the downbeat and the scene goes on.

* **Lap 1** is the scene's full phase by the stage table (drums alone; bass enters; drums return; bass strongest) with no route window, no hotspot window, no commit and no riser or fall: `choose()` is refused,
  `RunHotspots.shown` is empty (the final window needs `window_open`), `_hotspot_decision` makes no final commit, no door walk is latched and no passage frame closes. Its last block is judged like any other.
* **The boundary.** The stage of lap 2's first block is the stage of lap 1's last block, **one step on after a pass** (as at every block; `min(stage + 1, 3)`), so a player who earned the bass keeps it at its strongest:
  a perfect player's stages over the scene are 0 1 2 3 | 3 3 3 3, and a miss in the last block holds the stage. **Nothing is stripped back and nothing restarts**: `RunAudio` schedules nothing for a lap (its
  voices simply go on; every pack's phrase divides a 64-beat lap, which `RunData` validates), the engine emits a `mix` event at the boundary only if the stage changes and a `reveal` only if the bass enters on that very
  downbeat. A player who earned nothing in lap 1 starts lap 2 on drums alone and the stage table brings the bass in again from there: a second chance, never a harsher one. `bass_origin` is kept (it counts modulo the
  phrase, so lap 2's bass cues stay on the loop's own phrase) and the first block of lap 2 is charted at lap 1's last decision like any next block. The cue families of a perfect scene are drums, bass, drums, bass,
  then **bass for all four blocks of lap 2** (the stage holds at "bass strongest": drums 0.4, bass 1.0, synth 0.5). The part offsets (`part_offset`) carry on.
* **Lap 2 (the last lap)** is the phase as it always was from the player's side: hotspots on show from beat 49, the route window at beat 48 (riser if the strongest stage is in), the commit at the decision of the last
  block (beat 60.5), the route lock, the door walk (beat 61), the passage frame (beats 62 to 64), the tempo handoff: all at the LAST lap's beats, none of them moved or resized. **Hotspots are available in lap 2 only**
  (least risky: the 2 to 4 rule, `RunHotspots` and the whole hotspot contract are per scene and untouched; showing them in lap 1 would have needed a second, non-committing window state).
* **Leaving a path** (the pause menu's "Leave this path", beat 61 on) now also works in a lap before the last: the scene ends at that lap's downbeat, through the passage frame (`RunEngine.exit_pending()`).
* **Cast.** A scene's `cast` lines count `at_beat` from the scene's first downbeat across its laps: 0 to 64 x laps - 1 (`RunData.cast_last_beat`, `HotspotContract.validate_cast`'s `last_beat`). They are queued once when
  the scene begins and fire at `scene_t0 + at_beat * beat_s` as ever (stamped with the phase of the lap they fall in); a line of a later lap waits for its lap, so a stalled frame cannot fire it early. `block_fx`
  entries take an optional `lap` (1 to the scene's laps; default 1: an entry without it plays in the scene's first lap only, as it did).
* **The staging goes on.** The scene's lamps, set pieces, rail, people and the stage's `lights_*` actions are not reset at the boundary (`RunPlay._on_lap_start` only logs and clears the touch state; there is no
  `room_swell`, no `lights_low_pulse`, no pieces reset). `RunJourney` gives the lap's first block its glance and stroll and the rail keeps stepping, so the camera's walk goes on from where it was.
* **Counting scenes.** The result screen and the save's "best phases" count scenes (`run_over.scenes`), the scripted bots' routes are one per scene, `RW_RUN_UNTIL_PHASE` and the debug list's "back to the list when
  the scene ends" count scenes. `RunAudio` picks its bus pair from `phase - lap_extra`, so two scenes in a row still alternate pairs.

**Cast re-timing (tools/run/laps.py, called by the three generators).** The generators' tables still author one phase (beats 0 to 63); `laps.finish_run(run, laps, single)` writes `path.laps`, gives the
single-lap scenes `"laps": 1` and re-times the cast of the others: a line before beat 48 is spread over the laps (b x laps: 0, 16, 32 become 0, 32, 64; a line that holds 12 beats or more holds laps times as long, so
the person stays in the act until the next line takes over) and a line from beat 48 on (the last block: the window, the commit, the reactions at beat 61) keeps its place in the LAST lap (b + 64 for two laps). Nothing is
added or removed, so no text appears in play, and every reaction to a commit still lands at beats 125 to 127. After the change no cast beat lies between 96 and 111. Re-run
`python3 tools/content/make_gospel.py --run-only`, `python3 tools/paths/make_squadron.py` or `python3 tools/run/make_ember.py` after editing a table.

**Checks.** `tests/test_run_laps.gd` (the shipped laps, the validator, the window, commit and hotspots in the last lap only, the stage and cue families across the boundary, the bass phrase on the loop's own grid, a
missed block and a late reveal, the energy per block against the single-phase formula, the cast across laps at any frame step and across a stall, leaving in lap 1, the handoff after two laps and the Warehouse grid,
the main run without laps, the audio voices across the boundary, the real scene, the debug mode), `tools/content/test_laps.py`, `test_run_cast.gd`, `test_run_ember.gd`, `test_run_matrix.gd` (a scene of a path may take
twice as long; `RW_MATRIX_LAPS=1` replays the matrix at one lap), `python3 tools/run/check_hotspots.py --path <id>` (laps and cast ranges), `bash tools/run/walk_run.sh --path <id>` (the lap_start sequence of every
walk), `python tools/run/measure_mix.py --force-laps 1` (the before) against the data (the after), `tools/story/check_run_audio.py` (lap boundaries: no jump in the beat grid, no voice started there).

**Revert.** Set `path.laps` to 1 in `content/paths/<id>/run.json` (or change `LAPS` in the path's generator and re-run it: the cast goes back to its authored beats; the walks and tests follow the data). One value per
path; a scene's own `"laps": 1` stays. Nothing else in the data changes.
