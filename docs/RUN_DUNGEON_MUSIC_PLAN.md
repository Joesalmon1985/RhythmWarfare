# Plan for review: the continuous run, the Deathtrap Dungeon and new music on the 2.5D game

Status: APPROVED 2026-11-04 with the owner's calls recorded in section 2a. Work branch: `feature/run-on-25d`. Written against `main` at `1a4745a2` (the 2.5D polish) and the
branches `feature/continuous-story-run` and `feature/deathtrap-opening` (both cut from `5e1250a2`, the pre-polish `main`).

## 1. What the branches hold

`feature/deathtrap-opening` contains all of `feature/continuous-story-run` plus three dungeon commits, so it is the one to integrate. A trial
merge against the current `main` is clean (no conflicts). What it brings:

| Piece | What it is | State |
| --- | --- | --- |
| **Continuous run** (`src/run/`, `content/run/run.json`, `content/story/music.json`) | The story as one endless run: 64-beat phases at 174 BPM, drums alone then bass revealed by good play, a route choice in the last block (two arrows, a marked default), crowd energy as the survival meter, seven nodes over the five worlds (Warehouse > Mothership or Underworld > Hospital or Ward > the two "late" worlds that loop). Home screen becomes Play / Start from a reached level / Settings. Old chapter saves migrate. | Built, tested headless and recorded, screenshots. Never played by hand or on a phone. |
| **Beat Shaper import** (`tools/content/beatshaper.py`, `docs/MUSIC_IMPORT.md`, `docs/MUSIC_HANDOFF.md`) | One command imports a Drums/Bass/Synth WAV+MIDI set, measures its tempo (87 or 174 BPM profiles), cuts a loop, derives kick/snare and bass-hold cues in four difficulty tiers, assigns it to a level. A hand-off sheet says what to export per level. | Built, tested. |
| **Recorded packs** (`songs/packs/`) | Lv1 Warehouse, Lv1 Warehouse (1), Lv2 Alien Spaceship, Lv2 Alien Spaceship (2). Only the Warehouse and the Mothership play their own music; the Underworld, Hospital, Ward and late levels play stand-ins with filter/distortion/reverb treatments marked temporary. | Four more exports were rejected by the importer (bass out of line, wrong drum notes). |
| **Deathtrap Dungeon** (`src/trial/`, `content/trial/`, `assets/trial/`) | A gamebook dungeon entered from a wizard in the Warehouse: all 400 passages, four bars to choose per passage with a default, every choice is a rhythm phrase on the pads, fights are harder phrases (three losses end it), luck tests, 12 deaths, victory at 400. The music never stops. | Built and tested, but presented as a flat illustrated screen with placeholder pixel pictures, not in the 2.5D world. 28 passages are book-verified, 217 come from a noisy OCR graph, 155 are invented bridges. Text is original summaries. |

What the branches **lose** against the polished `main`: the run keeps the 2.5D worlds, crowds and pads but drives only one `player_move` per
level and a role; the chapter mode's performance-driven rails (dancer > stage > balcony > booth, or corridor > cubicle), the 23 activities by
mood, the glances in every block and the three endings per chapter are not used by the run. The run also hides the chapter mode and the
military campaign from the home screen (they stay in the repo).

## 2. The design calls I need from you

1. **Which game is the front door?** The run branch replaces the chapter campaign on the home screen. My recommendation: the run is the main
   game, but it must inherit the chapters' rail journeys and activities (section 4, WP-A3), and the chapter mode stays as "Story chapters" under
   Play rather than being hidden, because its endings and cutscenes are finished work.
2. **The dungeon's look.** Today it is a flat picture with floating text. Options: (a) keep it flat but with proper illustrations; (b) bring it into
   the 2.5D engine: each zone a small Doom-style map (crystal tunnel, galleries, Throm's pit, the vaults, the mirror gallery, Igbut's door), the
   camera on rails through it, creatures as pixel figures from the wardrobe system, choices as doors or paths you look at. I recommend (b): it is
   the same engine and pipeline, and it is what makes it part of this game rather than a bolt-on. Cost: about the size of two chapters.
3. **The dungeon's music.** It plays a Warehouse stand-in through a filter. It needs its own set (or two: ambient and fight). Can you export one?
4. **Deathtrap Dungeon is Ian Livingstone's book.** The branch avoids copying its text (original summaries, structure only) and uses the owner's
   earlier adaptations. For a game you release, the structure and names (Throm, Igbut, Bloodbeast, Sukumvit, the gems and the lock) are still
   the book's. Decide now whether this stays a private homage or gets renamed into an original "death trap dungeon" with your own creatures,
   zones and ending. The engine does not care; the content files do, and renaming is cheapest before more passages are written.
5. **Which 400?** Only 28 passages are verified and 155 are invented bridges. For a playable product I recommend a curated dungeon of about
   60 to 80 passages (the 28 verified plus hand-written ones along the zone spine), each with a real scene, rather than 400 of unequal quality.
6. **Music supply.** The hand-off sheet needs 4 chart sets plus 3 optional alternate renders to replace every stand-in, plus one or two for the
   dungeon. Four earlier exports were rejected. Do you want the importer loosened (bass placement by MIDI alone when the audio detector
   disagrees) or will you re-export?

## 2a. The owner's calls (2026-11-04)

1. Front door: the run is the main game; the chapters stay reachable under Play.
2. Dungeon look: **2.5D after all** (changed later on 2026-11-04, after the flat rename and curation landed): the Bassment's 16 zones become Doom-style maps on the story engine (WP-B2 to B4 now in scope, section 2b), and choosing "Enter the Trial" in the Warehouse is a **seamless transition**: no scene cut, no audio gap, no clock reset; the camera walks to the hatch and down into the first zone through the passage frame on a downbeat, the way the run swaps worlds.
3. Dungeon music: the owner supplies more music in `ToAddTry2/`; placeholders where more is needed.
4. Rights: **rename** the dungeon into an original death trap dungeon (zones, creatures, names, the lock) now.
5. Scope: **curated**, about 60 to 80 passages, agent's judgement on which.
6. Importer: **loosen** it (trust the MIDI when the audio detector disagrees; auto-detect kick and snare notes).
7. Delegation: Sonnet 5.5 subagents do the work where practical; Fable plans; Opus polishes later.

## 2b. The Bassment in 2.5D (WP-B2 to B4, revived)

- B2 Zone maps: one `content/story/maps/bassment_<zone>.json` per zone (Service Hatch, Cable Run, Lost Property, Flooded Boiler Room, Crystal Stacks, Barrel Cellar,
  Fungus Farm, Mirror Mezzanine, Reverb Pit, Vault of Records, Rat King's Warren, Furnace Kitchens, Hall of Hands, Resonance Door, Echo Chamber, Dawn Stair), each a
  small map of 2 to 4 sectors with the passage's choice points as visible exits (doors, ladders, gaps, water), distinct in footprint, height and light per the art brief,
  lit by placed light things (torches, crystal, furnace, water caustics as an animated surface), textured from generated tiles in a cellar palette (brick, pipe, barrel,
  crystal, fungus, mirror, iron). Zones are reused by every passage in them; a passage names its zone map and the waypoint it stands at.
- B3 The scene: `trial_play` hosts StoryStage worlds like the run does (prebuilt per zone, swapped on a downbeat through the passage frame), the camera on rails between
  passage waypoints; the four-bar window lights the exits for the choices and keeps the floating labels (phones); a pass walks through the chosen exit; a fail holds at the
  spot with a stumble; fights put the creature in the room as a figure with win and loss poses; deaths and the victory are tableaux (lights out, the dawn car park); the
  return to the Warehouse walks back up the hatch.
- B4 Figures: the ten creatures and the wizard drawn through the wardrobe and sheet bake (a creature set in the pipeline), the player's hands not shown.
- Seamless entry: the wizard's "Enter the Trial" during the Warehouse phase schedules a `player_move` to the hatch on the next cue-free guard, the hatch zone is prebuilt and
  its audio loaded on a thread while the window is open, and on the downbeat the camera walks through the passage frame into the Service Hatch with `RunAudio` continuing on
  the same clock (the dungeon's pack enters on that downbeat as a world's music does). No `change_scene`: the trial engine takes over the pads inside the run scene, or the
  trial scene adopts the live audio and clock; either way nothing restarts. Leaving by death or victory is the same walk in reverse, back to the Warehouse node.
- Tests: zone maps validate; every passage's waypoint and exits resolve; the entry and exit transitions keep the beat grid (recorded with record_music.gd: no restart, same
  delay); the dungeon walk by defaults on the real 2.5D scene; screenshots per zone and a contact sheet; frame numbers.

## 3. The target, in one paragraph

One game from the home screen: a continuous run through the five 2.5D worlds in which the music builds as you play well, the camera carries you
up or away on rails as it does in the chapters, the crowd behaves to the room and mood, and the route choice at the end of each phase is a
door you walk through. In the Warehouse a wizard offers the Trial: a Doom-style dungeon of its own zones and creatures, played on the same
pads with the same clock, four bars to choose at every passage, where death or victory returns you to the floor. Every level and the dungeon
play the owner's own recorded music through the one import command, with tiers of difficulty that rise with depth.

## 4. Work packages (Sonnet builds, Opus polishes, as before)

### WP-A Integrate the run on the polished main (branch `feature/run-on-25d`)
- A1 Merge `feature/deathtrap-opening` into a branch from `main`; run the full suite, the run recordings and the chapter walk-through; fix what the
  polish changed under the run (figure sheets, light sources, activities, settings). Keep both entry points reachable from home (call 2.1).
- A2 Music assignment check: every node plays, the Warehouse and Mothership on their own packs; the stand-ins labelled in the HUD's debug view.
- A3 **Rails and activities in the run.** Each run node gets a journey authored on the phase engine's events instead of the chapter decisions: at
  each block boundary a pass or hold moves the camera one step along the node's good rail (Warehouse: floor > steps > stage > balcony > booth) or
  back along its bad rail (floor edge > corridor > cubicle), with the queasy look and the sick beat on sustained holds; the route arrows become
  doors or paths in the room, lit when the window opens; the world swap is a walk through the door on the downbeat (the passage frame), not a
  flash. Glances and in-room walks in every block as the chapters have. Activities by mood band already follow energy, so they work unchanged.
- A4 Playtesting: the policy matrix on the run (perfect, accuracy 0.9 to 0.5, sloppy, none; seeds 1 to 3) asserting survival, depth reached and
  the rails taken; a run walk-through script through all seven nodes on the real scenes; screenshots per node and rail stop; frame numbers.

### WP-B The dungeon in 2.5D (branch `feature/dungeon-25d`)
- B1 Content decision applied (calls 2.4 and 2.5): the curated passage list, renamed or not, with a scene id per zone and a creature per fight.
- B2 Zone maps in the map format (`content/story/maps/dungeon_<zone>.json`): crystal entrance tunnel, the footprint galleries, the pit with a
  rope descent, the lower route, the trialmaster's chamber, the idol cavern, the drowned grotto, the vaults, the service tunnels, the mirror
  gallery, the lair, the grub tunnels, the troglodyte cavern, the manticore gate, Igbut's door with the three-gem lock, daylight. Each distinct
  in footprint, height and light per the art brief, with the choice points as visible exits.
- B3 `trial_play` on the 2.5D stage: the camera on rails between choice points; the four-bar window shows the choices as lit exits plus the
  floating labels (keep the labels, phones need the touch targets); a pass walks through; a fail holds at the spot; fights put the creature in the
  room as a pixel figure with win and loss poses; deaths and the victory as tableaux; return to the Warehouse by the passage frame.
- B4 Dungeon figures: creatures and the wizard through the wardrobe and sheet bake (an original bestiary if renamed); the player's hands are not
  shown (Doom shows a weapon; we show nothing or the pads).
- B5 Tests: the existing 19 trial tests ported; the four-bar window and default on the new scene; the dungeon walk-through by defaults (1 to 400
  or the curated end) on the real scene; screenshots per zone.

### WP-C Music (ongoing, each new export is one commit)
- C1 Importer hardening against the four rejected exports: a report that says exactly which bass notes failed and why; a `--trust-midi` mode that
  charts from the MIDI when the audio detector cannot place a wobbling bass (with a warning in `validate`), and `--kick`/`--snare` auto-detection
  from the most common low and mid notes.
- C2 The hand-off sheet regenerated for the run plus the dungeon (ambient and fight sets) and, if the chapters stay reachable, the chapters.
- C3 For every set you export: import, assign, validate, a scripted run on the node, a recording check, commit. Alternate renders for siblings
  where you provide them; treatments only as labelled stand-ins.
- C4 Tiers by ear: once real sets are in, a tuning pass of the four difficulty tiers (density, holds) against perfect and sloppy autoplay, so depth
  4 is hard but survivable.

### WP-D Opus polish
Dungeon zones to the art brief (dense dithered stone, torchlight pools, crystal glow, the mirror gallery's reflections, the lair's blood, daylight at
the end), the creatures, the choice-door lighting, the route windows in the five worlds, before/after sheets per zone.

### WP-E Release checks
A phone export and a by-hand play of one run and one dungeon trip on a device; memory of the sheets; calibration; the handover rewritten
around the run as the game.

## 5. Order and rough size

| Package | Depends on | Size (agent sessions) |
| --- | --- | --- |
| WP-A | your call 2.1 | 2 |
| WP-C1, C2 | nothing | 1 |
| WP-B | calls 2.2, 2.4, 2.5 | 3 |
| WP-C3, C4 | your exports | 1 per 2 to 3 sets |
| WP-D | WP-B | 1 to 2 |
| WP-E | all | 1 |

WP-A and WP-C1/C2 can start as soon as you answer 2.1; the dungeon waits on 2.2, 2.4 and 2.5.

## 6. Risks
- The run's phase engine and the chapters' director are two schedulers over the same stage; A3 must not run both. The run owns the stage in run
  mode; the director only in chapter mode.
- The dungeon's book-derived structure (2.4) is a rights question only you can settle; everything else in this plan is engine work.
- Frame time: a second scheduler and door lighting add little, but the dungeon zones are more maps with sheets; keep the 16 ms ceiling.
- Music: everything beyond the Warehouse and Mothership is a stand-in until you export; the game will sound like two songs until then.

## 7. Progress log

- **WP-B (dungeon rename and curation), done on the worktree branch cut from `feature/run-on-25d` (`da7ca3a8`).** The dungeon is now **The Bassment**, an original trial the wizard
  runs under the club: 63 hand-authored passages in 16 zones, 10 creatures, 7 luck tests, 6 deaths plus the defeat passage, 3 items that open secrets (a shortcut past the Fungus Farm, a
  way past the bouncer, a hidden seam past the gargoyle), one victory, and a final test of a held bass note then the Echo instead of a lock. The default choices alone walk 30 passages
  from the hatch to the victory. Removed from the working tree: `content/trial/{book_graph,book_text,quest_map}.json`, `src/trial/trial_book.gd`, the OCR build scripts,
  `docs/TRIAL_{FULL_BOOK,QUEST_MAP,PASSAGES}.md`, `docs/trial_quest_map.png`, the portraits copied from the owner's other repository and the status footer (git history still holds them).
  New: `tools/trial/make_scenes.py` and `make_creatures.py`; the validator now walks and checks the graph; the data format gained `items`, `grants` and `requires` (small, tested) and
  `music.fight_audio` / `fight_chart` (read and validated, equal to the dungeon's pack for now; the scene does not switch packs yet). `docs/TRIAL_OPENING.md` is the single dungeon doc;
  `tests/test_trial.gd` has 32 tests. Still to do after the merge: the run files still call the dungeon "the Trial" (`src/run/run_play.gd` button text and comments, `content/run/run.json`
  `trial_gate` value `deathtrap_opening`); assign the owner's `dd_part1` and `dd_part2` packs in `content/trial/passages.json` `music`; the flat screen has not moved into 2.5D (WP-B2 to B4
  stay deferred).
### WP-C Music (importer loosened, ToAddTry2 imported, run assigned, tiers retuned), 2026-11-04

Branch cut from `feature/run-on-25d` (`da7ca3a8`); four commits "Music, WP-C1" to "WP-C4". Written to be read on its own.

**C1, the importer** (`tools/content/beatshaper.py`, `test_beatshaper.py`, `docs/MUSIC_IMPORT.md`).
- Bass: if the audio bass detector cannot place the notes within 12 ms (median; it gives up at +-80 ms) the bass is charted from the MIDI timing with a warning;
  `--trust-midi` forces it. Both are recorded in `timing_report.json` (`timing.bass_timing.mode`: `audio_checked`, `midi_fallback`, `midi_flag`; the whole
  per-set report is under `import_report`). The loop audio is never moved.
- Tempo: a profile also verifies *loosely* (fitted tempo within 0.25 BPM, 85% of the hits within 12 ms, none over 40 ms); outliers are reported. Soft ghost
  snares were what rejected DD Part2, Lv4 Hospital (2), (3) and Lv5 Asylum.
- Kick and snare: 36 / 38 / 40, else automatic (hats 42/44/46 and cymbals skipped; most common note of the lower half = kick, of the upper half = snare), the
  choice reported; auto-mapped sets need the tempo within 0.1 BPM and 70% of hits in the limit. `--kick/--snare` override.
- Missing stems: Synth.wav missing = silent backing (reported); Synth.mid is never read. A set with WAVs but no MIDI is refused with what to export. **Lv3 Hell has
  the three WAVs (Drums, Bass, Synth) and none of the three MIDI files**, so it cannot be charted (the importer never charts from audio alone).
- A MIDI ending at 15.75 or 16.5 quarters is the 16-quarter phrase; cues that start after the loop end are dropped and reported.
- New `survey <folder>` command: every set measured, per-set decisions or the reason for refusal. Without `mido` (not installed here) a built-in MIDI reader is
  used (`common.py` imports mido optionally); `test_beatshaper.py` has a built-in MIDI writer and ran here: 20 tests OK. `test_content`, `test_export` and
  `test_import` still need mido and could not run here.

**C2, the sets** (`songs/packs/`). 16 new packs; the 4 existing re-import byte-identical (kept; their tiers 2 to 4 were later regenerated by C4).

| Set | Pack id | Result |
| --- | --- | --- |
| Lv1 Warehouse, (1) | `lv1_warehouse`, `_v1` | existing, byte-identical; clean (strict tempo, bass audio checked) |
| Lv1 Warehouse (2) | `lv1_warehouse_v2` | imported, **bass MIDI fallback** (detector median 48 ms) |
| Lv2 Alien Spaceship, (2) | `lv2_alien_spaceship`, `_v2` | existing, byte-identical; clean |
| Lv2 Alien Spaceship (1) | `lv2_alien_spaceship_v1` | imported via **auto drum notes** (39 kick, 43 snare: claps and toms only), loose tempo, bass fallback; sparse, weak chart |
| Lv2 Alien Spaceship (3) | `lv2_alien_spaceship_v3` | imported, bass fallback; **no kick note (36) in its MIDI: snare-only drum chart** |
| Lv3 Hell | `lv3_hell` | **not imported: three WAVs, no MIDI at all** (export Drums.mid and Bass.mid) |
| lv4 Hospital, (1) | `lv4_hospital`, `_v1` | clean |
| lv4 Hospital (2), (3) | `lv4_hospital_v2`, `_v3` | imported, loose tempo (ghost snares), bass audio checked |
| Lv5 Asylum | `lv5_asylum` | imported, loose tempo, bass fallback |
| Lv5 Asylum (1), (2), (3) | `lv5_asylum_v1`, `_v2`, `_v3` | imported, bass fallback (a note at quarter 16.25 past the loop dropped in v1) |
| DD Part1 | `dd_part1` | clean |
| DD Part1 (1), (2) | `dd_part1_v1`, `_v2` | clean |
| DD Part1 (3) | `dd_part1_v3` | imported, bass fallback |
| DD Part2 | `dd_part2` | imported, loose tempo, bass fallback |
| Default Project | - | skipped (template) |

**C3, the assignment** (`content/story/music.json`; no treatments; `temporary` only for the underworld).

| Node | Depth / tier | audio = chart | Own music |
| --- | --- | --- | --- |
| warehouse | 1 | `lv1_warehouse` | yes |
| mothership | 2 | `lv2_alien_spaceship` | yes |
| underworld | 2 | `lv2_alien_spaceship_v2` (alternate Lv2 take; Lv3 Hell cannot be charted yet) | **no, placeholder** |
| hospital | 3 | `lv4_hospital` | yes |
| ward | 3 | `lv5_asylum` | yes |
| hospital_late | 4 | `lv4_hospital_v1` | yes |
| ward_late | 4 | `lv5_asylum_v2` | yes |

Changed in `src/run/run_data.gd` (4 lines): the check "nodes at one depth use different charts" appends to `warnings` instead of `errors`; the message now says "siblings no
longer share one chart (both play tier N of their own pack)". `beatshaper.py validate` prints the same as a `WARNING` line. Tests touched by that (the run agent's files,
please reconcile on merge): `tests/test_run_progress.gd` (the default data's warnings are filtered to "cannot be reached"; the sibling-chart case asserts a warning),
`tests/test_run_engine.gd` (the "siblings share a chart" test became "every node has its tier" and the "identical required cues" test became "each sibling charts
its own pack's block-1 cues at the same tier").

**Engine caveat the coordinator must decide (not changed here, `src/run/` is not mine):** `RunEngine._chart_next_phase` charts block 0 of the next phase (drums alone)
at the last block's decision beat from the *default* route's chart, before the player's choice is final, because siblings used to share a chart. With different
charts a player who picks the non-default route plays the chosen world's recording over the default world's block-0 cues (blocks 1 to 3 use the chosen node's own chart;
the test above deliberately checks block 1). Suggested fix: chart block 0 from `selected_route()` instead of `default_route()` at that beat and refuse
`choose()`/`choose_dir()` to a route with a different chart afterwards (or move the lock a few beats before the end of the phase and show it in the HUD).

**Dungeon** (`content/trial/passages.json` not edited): imported `dd_part1` (ambient, 87 BPM x2, 32 beats; variants `_v1` `_v2` `_v3`) and `dd_part2` (fight, 174 BPM, 16 beats).
Suggested assignment: `"music": {"audio": "dd_part1", "chart": "dd_part1", "treatment": "none", "temporary": false}`, and `dd_part2` for fight phrases if the trial engine learns
to switch packs. `beatshaper.py assign` does not cover the trial block, so after the merge edit the `music` object of `content/trial/passages.json` by hand and run
`python3 tools/content/beatshaper.py validate`. Also in `docs/MUSIC_HANDOFF.md`.

**C4, verification.**
- `python3 tools/content/beatshaper.py validate`: OK, with three sibling-chart WARNING lines (depths 2, 3, 4) as intended.
- Recording check (real `run_play` scene, `RW_RUN_START=<node> RW_RUN_BOT=perfect`, `record_music.gd` 50 s + `check_run_audio.py`), every assigned node, 2 phases each: all 9
  fitted blocks per node explained (minimum 94.9 to 99.9% of the signal, fitted gains within 0.12 of the stage table), delay spread within a run 5.9 ms (one mix chunk), bass and
  synth 0.0 to 11.8 ms from the drums: warehouse, mothership, underworld, hospital, ward, hospital_late, ward_late all RESULT ok. The first `ward_late` recording (taken while
  another Godot job loaded the machine) showed its first phase starting its voices 80 ms late (RESULT CHECK); the repeat was clean (spread 5.9 ms), so a start-up stall, not the pack.
- Godot suite (`tools/test.sh`): 41152 checks, the only 4 failures were in my own new engine test (it did not play long enough to chart block 1); fixed, `--filter run_` then
  124 checks, 0 failures. The Python `unittest discover` of `tools/content` shows 3 errors, all `ModuleNotFoundError: mido` (test_content, test_export, test_import).
- Tier tuning (`tools/story/tune_run.gd`: `godot --headless --path . -s tools/story/tune_run.gd -- 1.0,0.9,0.8,0.7,0.6,0.5 5 15 [jitter_ms]`; the engine with a scripted player that hits
  each cue with probability a, on time, optionally with gaussian timing jitter). **Before**, the tiers were not nested and often identical (tier 1 = 2 and tier 3 = 4 in most packs: drum
  min gaps 1.0/0.75/0.5/0.5 beats, bass 2/1.5/1/0.75). **Now** (`BASE_GAP`, `FULL_GAP`, `TIER_SHARE` in `beatshaper.py`): tier 1 = whole beats at least a beat apart (bass two), tier 4 =
  everything at least half a beat apart, tiers 2 and 3 add a third and two thirds of the cues in between; each tier contains the one below. Cues a perfect run is asked for per 64-beat
  phase, by tier 1/2/3/4: `lv1_warehouse` 20/20/22/24, `lv2_alien_spaceship` 30/36/44/52, `lv2_alien_spaceship_v2` 34/48/62/76, `lv4_hospital` 34/36/38/42, `lv4_hospital_v1` 28/34/38/48,
  `lv5_asylum` 18/20/24/28, `lv5_asylum_v2` 26/28/30/32. **By node** (own tier): warehouse 20, mothership 36, underworld 48, hospital 38, ward 24, hospital_late 48, ward_late 32. Density
  rises with depth along every lineage and on average from depth 1 to 2 and 4, but the Ward (the Asylum is sparse: 26 drum notes in 32 beats) is thinner than the depth-2 worlds, so depth 3
  averages 31 against 42 at depth 2. Thinning cannot add cues a MIDI does not have: export a denser Asylum or give the Ward `lv5_asylum_v2` (30 at tier 3).
  Survival (5 seeds x 15 phases, always the default route, a = chance of hitting each cue): every node reaches phase 16 at a = 1.0 to 0.6 (also with 45 ms of timing jitter) and fails before it at 0.5
  (0 or 1 of 5 runs reach 16), minimum crowd energy 56 to 60 at a = 0.8 and 28 to 50 at 0.6. Blocks passed at a = 0.8: depth 1 75%, depth 2 98 to 100%, depth 3 85 to 91%, depth 4 88 to 91%
  (a block's pass depends on its cue count more than its tier). So depth 4 is survivable at 0.8 with ease and only collapses near 0.5: it is **not hard yet** under this miss-only player. The
  survival meter (`content/run/run.json` `energy`: start 60, pass +5..11, fail -3..10) is what makes it forgiving; it is not my file, so it is untouched. Tune `fail_loss` or `pass_credit` there after a hand play.
- Not done: nothing was listened to (the recordings prove timing and mix, not taste); the block-0 caveat above; Lv3 Hell.
### WP-A (branch worktree-agent-a64188e6721b262ab, cut from feature/run-on-25d at da7ca3a8), 2026-11-04

* **A1 verify the merge.** Suite 41,143 checks, 0 failures; chapter walk-through OK on all five paths; the 26 trial tests pass; the run recording check failed its mix fit on the Warehouse. Cause: a 2.5D stage
  build decoded sixteen 2048 px people pages on the main thread (0.8 to 2.4 s), swallowing the cue-free guard in which the run builds the next world and delaying `RunAudio`'s gain changes. Fix:
  `StoryPeople.prewarm()` on a worker thread (builds 0.5 to 0.7 s). Re-recorded fits within 0.01 of the table. The per-phase delay spread (15 to 25 ms) needs re-measuring on an idle machine.
* **A2 home screen.** Play, Story chapters, Start from a reached level, Settings; the military campaign, loadout and duel (including the Loadout button in the chapter menu) are developer-only; compact
  layout for short windows; the chapter menu is titled STORY CHAPTERS. `tests/test_run_home.gd`.
* **A3 rails and activities.** `rail` per node in run.json; `RunRail`, `RunJourney`, `RunPassage` (pure), `RunPassageView`, `RunExitsView`; glances and strolls in every block; lit exits beside the touch
  arrows; the world swap is a closing and opening doorway frame with a walk in from the new world's doorway. Activities were already energy-driven (confirmed by test). Route lock added for levels that chart
  different packs (see CONTINUOUS_RUN.md). `tests/test_run_rail.gd`, `test_run_rail_scene.gd`, `test_run_lock.gd`.
* **A4 playtests.** `tests/test_run_matrix.gd` (7 policies x seeds 1 to 3), `tools/run/walk_run.sh` (all seven levels, isolated saves), `tools/run/capture.sh` (80 screenshots in docs/shots/run),
  `tools/run/frames.sh` and `profile_build.tscn`. Results in CONTINUOUS_RUN.md.
* **Deviations.** The fourth rail step of a phase is cut by the world swap 3.5 beats later (the booth shows only in loops); the dense-run rule is enforced by shortening moves to 2 bars rather than moving them;
  the world swap does not close the frame for same-world routes; frame numbers were taken on a loaded machine; the run is forgiving (accuracy 0.7 survives), tuning left to WP-C4.
* **Merge notes.** `tests/test_run_engine.gd` and `test_run_progress.gd` were not touched here (the music branch's edits merge cleanly); `content/run/run.json` is only changed here (a `rail` per node);
  `run_data.gd` gained one validation line (the music branch edits the chart-sibling check nearby).
### WP-B 2.5D (B2 to B6, the Bassment in the story engine, seamless entry and exit), 2026-11-04

Branch cut from `feature/run-on-25d` (`77060085`); commits "Bassment 2.5D, B2 prep", "B2 zone maps", "B3 to B5 ...", and the B6 commit (tests, docs, shots). Written to be read on its own; `docs/TRIAL_OPENING.md` is the user-facing doc.

* **B2 zone maps.** `content/story/maps/bassment_<zone>.json` for all 16 zones (2 to 4 sectors each, `"art": "bassment"`; `StoryMap.load_chapter` now reads an optional `art` key so maps can share one art folder), authored by four
  Sonnet subagents from a brief (their generators were scratch scripts, only the JSON is in the repo), with `content/trial/layout/<zone>.json` (authoring form of the passages' places) applied by `tools/trial/apply_layout.py`.
  Each passage now has `map` and `waypoint`, each choice `exit_wp` (deviation: the brief said `exit`, but `exit` is already the way out of the dungeon on death/victory choices). `TrialData` validates all of it
  (`tools/trial/check_maps.gd` per zone). The art set `assets/story/bassment/` (86 textures: cellar-palette tiles, props, a dawn sky, creature figures) is `tools/story/art/tex_bassment.py`; the zones' look is in TRIAL_OPENING.md.
* **B4 figures (deviation).** The ten creatures and the wizard are billboard things (idle, attack, struck frames, 128 px) built from the existing 64 px portraits, not wardrobe rigs and sheets (creatures need no skeleton); sized and lifted per creature
  (`TrialScene.FIGURES`), animated by song time (bob and beat pulse, lunge with a red rim on a lost phrase, struck then sink and fade on a win).
* **B3 the scene.** `src/trial/trial_scene.gd` (`TrialScene`) is hosted by `RunPlay`: one `StoryStage` per zone (built in a cue-free guard at the commit of a choice for the zone it leads to, or on demand; at most four kept), swapped on a block
  downbeat through the passage frame; rails (`player_move` to the exit, then to the next waypoint; glance, queasy and stumble on a fail; look down and fade on death, flash and warm light on victory); the choices stay floating buttons (keys 1 to 4) and
  are also lit in the room as numbered exits through `RunExitsView`. `trial_play.tscn` is now a launcher into the run scene (`Session.trial_direct`); `RW_TRIAL_*` env variables still work. The flat scene pictures are not shown any more (kept in `assets/trial/scenes`).
* **B5 the seamless transitions.** Built as described in TRIAL_OPENING.md ("The seamless entry and exit"): `RunPlay.arm_trial` (guard 12.75 of the next block: walk to the Warehouse map's new `hatch` waypoint; the guard after: `trial_begin_now`, the pads
  re-bound to the trial engine whose `origin` is the entry downbeat; the downbeat: the frame opens in the Service Hatch and `RunAudio` gets a `phase_start` for `dd_part1`), `trial_leave` and `RunEngine.resume` (new: fresh level and judge, energy and phase
  count kept, ticks absolute). The dungeon takes a phase number so the audio bus pairs alternate. Limits: the wizard can only be chosen up to beat 44 of the Warehouse phase; after the entry the HUD is hidden and the run's journey is not applied.
  Engine fix on the way: `TrialEngine.count_in_s` is relative (a version with the origin added gave a 16-second first window).
* **Recording** (real time, headless dummy driver, `RW_TRIAL_ENTER=1 RW_TRIAL_LEAVE_AT=30`, `tools/trial/check_transition_audio.py`; the bot re-enters after every return, so there are four visits): one drums voice per stretch
  (`warehouse` 0.0, `trial` 11.034, `warehouse` 33.103, `trial` 44.138, ...), every group entered on the 16-beat grid of its predecessor, no restart and no gap in the clock stream. Drums delay against each pack's loop (ms): Warehouse -130.6,
  dungeon -127.6, Warehouse -109.9, dungeon -121.7, Warehouse -121.7, dungeon -118.8, Warehouse **-59.9**, dungeon -115.8: seven of eight within 21 ms, the eighth (the third return, voice started 41 ms late) 60 ms off, so the same-delay
  criterion (12 ms) is **not met in the recording** (RESULT CHECK); the first group is not far from the later ones, so the offset is a start-up/lateness effect (the voices are compensated by how late they start), probably a main-thread
  stall at the swap on a loaded machine. Needs a re-run on an idle machine and a look at what runs on the return frame.
* **Tests and walks.** `tests/test_trial.gd` 38 tests (the scene tests ported to the run scene, plus map/waypoint/exit validation and reachability, zone swaps on a downbeat, the entry, the exit by the back key with energy kept); `bash tools/trial/walk_trial.sh`
  prints `WALK OK` (Warehouse > wizard > hatch > 16 zones to Daylight at 330 s of song time > back in the Warehouse at phase 3, energy 82). Two run tests fail on this branch for reasons outside this work package (the music branch's per-node chart packs:
  `test_run_lock` last assertion, `test_run_matrix` accuracy:0.5 glance check); they are listed with the full-suite result below.
* **Frame times** (windowed 1280x720, vsync off, perfect autoplay, `tools/trial/frames.sh`): cellar 9.7 ms mean (p95 12.5, max 18), stacks 9.4 (11.0, 21), fungus 9.3 (11.1, 22), mirrors 9.5 (11.2, 22); none over 50 ms. A zone swap builds one stage
  (about 0.1 to 0.3 s) in the guard; not measured separately.
* **Screenshots**: `docs/shots/trial/contact_bassment.jpg` (16 zones), `zone_<zone>.png`, `entry_1..5`, `fight_1_eel`, `fight_2_eel_lunges`, `death_tableau`, `victory_tableau`.
* **For the polish agent.** The text panel covers a third of the view (make it collapsible or fade it after a bar); the zone maps' cameras have no pitch (the hatch, shaft and pit read across, not down); dark zones (warren, echo, cellar floor); the cars and the
  sandwich of the dawn zone; the flat scenes and `make_scenes.py` can be deleted; exit markers are plain rectangles (a lit door sprite would be better); the creatures are enlarged portraits; fight music (`dd_part2`) is still not switched to; the wizard figure
  is not placed in the hatch zone.
